import contextlib
import sys
import termios
import argparse
import asyncio
import os
import json
from typing import Union
import websockets
from solana.rpc.types import TxOpts
from spl.token.instructions import (
    create_associated_token_account,
    get_associated_token_address,
)
from spl.token.constants import TOKEN_PROGRAM_ID, WRAPPED_SOL_MINT
from solders.keypair import Keypair
from solders.instruction import Instruction
from solana.transaction import Transaction
from solana.transaction import AccountMeta
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
import time

from phoenix.client import PhoenixClient
from phoenix.market import Ladder, Market
from phoenix.market_metadata import MarketMetadata
from phoenix.order_subscribe_response import (
    CancelledOrder,
    FilledOrder,
    OpenOrder,
    OrderSubscribeError,
)
from phoenix.types.fifo_order_id import FIFOOrderId
from phoenix.types.side import Ask, Bid
from binance import AsyncClient, BinanceSocketManager

BID_CLIENT_ORDER_ID = 0x0B
ASK_CLIENT_ORDER_ID = 0x0A


class Bot:
    def __init__(
        self,
        signer: Keypair,
        client: PhoenixClient,
        market: Pubkey,
        edge_in_basis_points=5,
        quote_size=25,
    ):
        self.signer = signer
        self.phoenix_client = client
        self.market = market

        self.edge_in_basis_points = edge_in_basis_points
        self.quote_size = quote_size

        self.is_running = True
        self.fair_price = None
        self.bids = []
        self.asks = []

        self.usdc_usdt = 1.0
        self.coinbase_vwap = None
        self.binance_vwap = None
        self.phoenix_best_bid = None
        self.phoenix_best_bid_size = None
        self.phoenix_best_ask = None
        self.phoenix_best_ask_size = None
        self.is_running = False
        self.sequence_number = -1
        self.metadata: Union[MarketMetadata, None] = None

        self.offset_in_bps = 0

        self.market_snapshot = None
        self.__updating_quotes = False

    async def initialize(self):
        await self.phoenix_client.add_market(self.market)
        self.is_running = True
        self.metadata = self.phoenix_client.markets[self.market]

        if (
            self.metadata.quote_mint == WRAPPED_SOL_MINT
            or self.metadata.base_mint == WRAPPED_SOL_MINT
        ):
            sol_ata = get_associated_token_address(
                self.signer.pubkey(),
                WRAPPED_SOL_MINT,
            )

            wallet_balance = (
                await self.phoenix_client.client.get_balance(
                    self.signer.pubkey(), commitment="confirmed"
                )
            ).value
            print("Wallet balance:", wallet_balance)

            balance = await self.phoenix_client.client.get_balance(
                sol_ata, commitment="confirmed"
            )
            print("ATA balance:", balance.value)

            if balance.value < 2e9:
                transaction = Transaction()
                # Top up the WSOL account with SOL and keep 1 SOL for gas
                print(int(wallet_balance - 1e9))
                transfer_ix = transfer(
                    TransferParams(
                        from_pubkey=self.signer.pubkey(),
                        to_pubkey=sol_ata,
                        lamports=int(wallet_balance - 1e8),
                    ),
                )
                transaction.add(transfer_ix)
                signature = (
                    await self.phoenix_client.client.send_transaction(
                        transaction,
                        self.signer,
                        opts=TxOpts(skip_preflight=True),
                    )
                ).value
                await self.phoenix_client.client.confirm_transaction(
                    signature, "confirmed"
                )

    async def get_fair_price_from_coinbase(self):
        if not self.is_running:
            raise Exception("Bot not initialized")
        # Get price feed from Coinbase (SOL-USD)
        # In reality, you would want to get the price feed from multiple sources
        async with websockets.connect("wss://ws-feed.pro.coinbase.com") as ws:
            await ws.send(
                json.dumps(
                    {
                        "type": "subscribe",
                        "product_ids": [
                            "SOL-USD",
                        ],
                        "channels": [
                            "heartbeat",
                            {"name": "ticker", "product_ids": ["SOL-USD"]},
                        ],
                    }
                )
            )
            while self.is_running:
                try:
                    data = await ws.recv()
                    if data != "":
                        price_feed = json.loads(data)
                        if "best_bid" not in price_feed:
                            continue
                        best_bid = float(price_feed["best_bid"])
                        best_ask = float(price_feed["best_ask"])
                        best_bid_size = float(price_feed["best_bid_size"])
                        best_ask_size = float(price_feed["best_ask_size"])
                        self.coinbase_vwap = (
                            best_bid * best_ask_size + best_ask * best_bid_size
                        ) / (best_bid_size + best_ask_size)
                        await self.update_quotes()
                    else:
                        print("Received empty message")
                except ValueError as e:
                    print(e)
                except Exception as e:
                    print(e)

    async def get_fair_price_from_binance(self):
        client = await AsyncClient.create()

        bm = BinanceSocketManager(client)
        ts = bm.symbol_book_ticker_socket("SOLUSDT")
        async with ts as tscm:
            while self.is_running:
                try:
                    price_feed = await tscm.recv()
                    best_bid = float(price_feed["b"])
                    best_ask = float(price_feed["a"])
                    best_bid_size = float(price_feed["B"])
                    best_ask_size = float(price_feed["A"])
                    self.binance_vwap = (
                        (1 / self.usdc_usdt)
                        * (best_bid * best_ask_size + best_ask * best_bid_size)
                        / (best_bid_size + best_ask_size)
                    )
                    await self.update_quotes()
                except:
                    continue

        await client.close_connection()

    async def get_usdc_usdt_price(self):
        client = await AsyncClient.create()
        while self.is_running:
            try:
                data = await client.get_symbol_ticker(symbol="USDCUSDT")
                usdc_usdt = float(data["price"])
                if abs(1 - usdc_usdt) > 0.01:
                    (signature, _) = await self.phoenix_client.cancel_orders(
                        self.signer, market_pubkey=self.market, withdraw_free_funds=True
                    )
                    print(f"https://solscan.io/tx/{signature}")
                    self.is_running = False
                    print("Cancelled all orders and exiting program.")
                self.usdc_usdt = usdc_usdt
                await asyncio.sleep(2)
            except:
                await asyncio.sleep(2)

    async def order_subscribe(self):
        async for event_packet in self.phoenix_client.order_subscribe(
            self.market, self.signer.pubkey(), "processed"
        ):
            for event in event_packet:
                if isinstance(event, FilledOrder):
                    print("Fill:", event.taker_side, event.price, event.quantity_filled)
                if isinstance(event, OrderSubscribeError):
                    print("Error", event)

    async def order_subscribe_with_default_client(self):
        async for event_packet in self.phoenix_client.order_subscribe_with_default_client(
            self.market,
            self.signer.pubkey(),
        ):
            for event in event_packet:
                if isinstance(event, FilledOrder):
                    print("Fill:", event.taker_side, event.price, event.quantity_filled)
                if isinstance(event, OrderSubscribeError):
                    print("Error", event)

    async def update_quotes(self, force=False, attempts=1):
        if attempts > 3:
            print("Failed to update quotes, attempted 3 times")
            self.__updating_quotes = False
            return
        self.__updating_quotes = True
        starting_orders = []
        starting_orders.extend(self.bids)
        starting_orders.extend(self.asks)
        starting_orders = [FIFOOrderId.from_int(i.order_id) for i in starting_orders]

        fair = (
            self.binance_vwap if self.binance_vwap is not None else self.coinbase_vwap
        )
        if fair is None:
            return
        fair *= 1 + (self.offset_in_bps / 10000)

        if len(starting_orders) == 2:
            bid = self.metadata.ticks_to_float_price(starting_orders[0].price_in_ticks)
            ask = self.metadata.ticks_to_float_price(starting_orders[1].price_in_ticks)
            mid = (bid + ask) / 2
            edge = mid * (self.edge_in_basis_points / 10000)

            if not force and abs(fair - mid) <= edge * 0.25:
                return

        print(
            "Coinbase fair price:",
            self.coinbase_vwap,
            "Binance fair price:",
            self.binance_vwap,
        )

        bid_price = fair * (1 - (self.edge_in_basis_points / 10000))
        bid = self.phoenix_client.get_post_only_order_packet(
            self.market,
            Bid,
            bid_price,
            self.quote_size / bid_price,
            client_order_id=BID_CLIENT_ORDER_ID,
            fail_silently_on_insufficient_funds=True,
        )
        ask_price = fair * (1 + (self.edge_in_basis_points / 10000))
        ask = self.phoenix_client.get_post_only_order_packet(
            self.market,
            Ask,
            ask_price,
            self.quote_size / ask_price,
            client_order_id=ASK_CLIENT_ORDER_ID,
            fail_silently_on_insufficient_funds=True,
        )
        pre_instructions = []

        if (
            self.metadata.quote_mint == WRAPPED_SOL_MINT
            or self.metadata.base_mint == WRAPPED_SOL_MINT
        ):
            base_create_ata_instruction = create_associated_token_account(
                self.signer.pubkey(),
                owner=self.signer.pubkey(),
                mint=WRAPPED_SOL_MINT,
            )
            # Create ATA instruction idempotently
            create_ata_instruction = Instruction(
                program_id=base_create_ata_instruction.program_id,
                accounts=base_create_ata_instruction.accounts,
                data=b"\x01",
            )

            sync_native_instruction = Instruction(
                program_id=TOKEN_PROGRAM_ID,
                accounts=[
                    AccountMeta(
                        get_associated_token_address(
                            self.signer.pubkey(), WRAPPED_SOL_MINT
                        ),
                        False,
                        True,
                    ),
                ],
                data=b"\x11",
            )
            pre_instructions.append(create_ata_instruction)
            pre_instructions.append(sync_native_instruction)

        cancel_instruction = self.phoenix_client.create_cancel_order_instruction(
            self.signer.pubkey(), self.market, withdraw_funds=False
        )
        pre_instructions.append(cancel_instruction)
        response = await self.phoenix_client.send_orders(
            signer=self.signer,
            order_packets=[bid, ask],
            pre_instructions=pre_instructions,
            tx_opts=TxOpts(skip_preflight=True),
        )

        if response is None:
            return await self.update_quotes(attempts=attempts + 1)

        self.sequence_number = max(response.sequence_number, self.sequence_number)
        print(f"https://solscan.io/tx/{response.signature}")
        if ASK_CLIENT_ORDER_ID in response.client_orders_map:
            if response.client_orders_map[ASK_CLIENT_ORDER_ID] is not None:
                self.asks = [response.client_orders_map[ASK_CLIENT_ORDER_ID]]

        if BID_CLIENT_ORDER_ID in response.client_orders_map:
            if response.client_orders_map[BID_CLIENT_ORDER_ID] is not None:
                self.bids = [response.client_orders_map[BID_CLIENT_ORDER_ID]]

        placed_bid_price = None
        placed_bid_size = None
        if len(self.bids) > 0:
            placed_bid_price = self.metadata.ticks_to_float_price(
                FIFOOrderId.from_int(self.bids[0].order_id).price_in_ticks
            )
            placed_bid_size = self.metadata.base_lots_to_raw_base_units_as_float(
                self.bids[0].base_lots_remaining
            )

        placed_ask_price = None
        placed_ask_size = None
        if len(self.asks) > 0:
            placed_ask_price = self.metadata.ticks_to_float_price(
                FIFOOrderId.from_int(self.asks[0].order_id).price_in_ticks
            )
            placed_ask_size = self.metadata.base_lots_to_raw_base_units_as_float(
                self.asks[0].base_lots_remaining
            )

        print(
            "Our market:",
            placed_bid_size,
            placed_bid_price,
            "@",
            placed_ask_price,
            placed_ask_size,
        )

        self.__updating_quotes = False

    async def hearbeat(self):
        while self.is_running:
            print("Heartbeat")
            await asyncio.sleep(5)

    async def handle_l2_orderbook(self, book: Ladder):
        if not self.is_running:
            return
        if len(book.bids) == 0:
            self.phoenix_best_bid = None
            self.phoenix_best_bid_size = None
        else:
            self.phoenix_best_bid = book.bids[0].price
            self.phoenix_best_bid_size = book.bids[0].size
        if len(book.asks) == 0:
            self.phoenix_best_ask = None
            self.phoenix_best_ask_size = None
        else:
            self.phoenix_best_ask = book.asks[0].price
            self.phoenix_best_ask_size = book.asks[0].size

    async def handle_market(self, market: Market):
        if not self.is_running:
            return
        if market.sequence_number <= self.sequence_number:
            return
        self.market_snapshot = market
        if self.__updating_quotes:
            return
        self.sequence_number = market.sequence_number
        trader_index = market.trader_pubkey_to_trader_index.get(
            self.signer.pubkey(), None
        )
        if trader_index is None:
            return
        found_bid = False
        found_ask = False
        ask = None
        bid = None
        if len(self.bids) > 0:
            bid = self.bids[0]
            bid_order_id = FIFOOrderId.from_int(bid.order_id)
            for order in market.bids:
                if order[1].trader_index != trader_index:
                    continue
                if order[0].order_sequence_number == bid_order_id.order_sequence_number:
                    found_bid = True
                    break
            if not found_bid:
                self.bids = []
        else:
            found_bid = True
        if len(self.asks) > 0:
            ask = self.asks[0]
            ask_order_id = FIFOOrderId.from_int(ask.order_id)
            for order in market.asks:
                if order[1].trader_index != trader_index:
                    continue
                if order[0].order_sequence_number == ask_order_id.order_sequence_number:
                    found_ask = True
                    break
            if not found_ask:
                self.asks = []
        else:
            found_ask = True

        if not found_bid or not found_ask:
            await self.update_quotes(force=True)

    async def l2_book_subscribe(self):
        if not self.is_running:
            raise Exception("Bot not initialized")
        await self.phoenix_client.l2_orderbook_subscribe(
            self.market, self.handle_l2_orderbook
        )

    async def market_subscribe(self):
        if not self.is_running:
            raise Exception("Bot not initialized")
        await self.phoenix_client.market_subscribe(self.market, self.handle_market)

    """
    If you press the down arrow in the terminal, it will shift the fair price down by 1 tick    
    If you press the up arrow in the terminal, it will shift the fair price up by 1 tick    
    If you press the enter key in the terminal, it will trigger a quote update 
    If you press the backspace key in the terminal, it will reset the offet 
    """

    async def offset_subscribe(self):
        with raw_mode(sys.stdin):
            reader = asyncio.StreamReader()
            loop = asyncio.get_event_loop()
            await loop.connect_read_pipe(
                lambda: asyncio.StreamReaderProtocol(reader), sys.stdin
            )
            prev = None
            while not reader.at_eof():
                ch = await reader.read(1)
                # '' means EOF, chr(4) means EOT (sent by CTRL+D on UNIX terminals)
                if not ch or ord(ch) <= 4:
                    break

                # handle enter key
                if ch == b"\n":
                    prev = None
                    await self.update_quotes(force=True)
                # handle backspace key
                elif ch == b"\x7f":
                    prev = None
                    print(f"Offset Reset {self.offset_in_bps} -> 0")
                    self.offset_in_bps = 0
                    await self.update_quotes(force=True)
                elif ch == b"x":
                    print("Cancelling all orders")
                    await self.phoenix_client.cancel_orders(
                        self.signer, market_pubkey=self.market
                    )
                elif ch == b"q":
                    (signature, _) = await self.phoenix_client.cancel_orders(
                        self.signer, market_pubkey=self.market, withdraw_free_funds=True
                    )
                    print(f"https://solscan.io/tx/{signature}")
                    self.is_running = False
                    print("Cancelled all orders and exiting program.")
                elif ch == b"v":
                    # Print trader info
                    if self.market_snapshot is None:
                        continue
                    trader_index = (
                        self.market_snapshot.trader_pubkey_to_trader_index.get(
                            self.signer.pubkey(), None
                        )
                    )
                    if trader_index is None:
                        print("Trader not found in market")
                        continue
                    # Print wallet balance
                    wallet_balance = (
                        await self.phoenix_client.client.get_balance(
                            self.signer.pubkey(), commitment="confirmed"
                        )
                    ).value
                    print("\nAddress:", self.signer.pubkey())
                    print(
                        f"Current offset: {'+' if self.offset_in_bps> 0 else ''}{self.offset_in_bps} bps"
                    )
                    print("Wallet balance:", wallet_balance / 1e9)

                    # Print base balance
                    base_ata = get_associated_token_address(
                        self.signer.pubkey(),
                        WRAPPED_SOL_MINT,
                    )
                    balance = await self.phoenix_client.client.get_balance(
                        base_ata, commitment="confirmed"
                    )
                    print("Base mint:", self.metadata.base_mint)
                    print(
                        f"\tBase wallet balance:",
                        balance.value / 10**self.metadata.base_decimals,
                    )
                    trader_state = self.market_snapshot.traders[self.signer.pubkey()]
                    print(
                        f"\tBase locked balance:",
                        self.metadata.base_lots_to_raw_base_units_as_float(
                            trader_state.base_lots_locked
                        ),
                    )
                    print(
                        f"\t  Base free balance:",
                        self.metadata.base_lots_to_raw_base_units_as_float(
                            trader_state.base_lots_free
                        ),
                    )
                    print()
                    print("Quote mint:", self.metadata.quote_mint)
                    quote_ata = get_associated_token_address(
                        self.signer.pubkey(),
                        self.metadata.quote_mint,
                    )
                    balance = (
                        await self.phoenix_client.client.get_token_account_balance(
                            quote_ata, commitment="confirmed"
                        )
                    )
                    print(
                        "\tQuote wallet balance:",
                        balance.value.ui_amount_string,
                    )
                    print(
                        "\tQuote locked balance:",
                        self.metadata.quote_lots_to_quote_units(
                            trader_state.quote_lots_locked
                        ),
                    )
                    print(
                        "\t  Quote free balance:",
                        self.metadata.quote_lots_to_quote_units(
                            trader_state.quote_lots_free
                        ),
                    )
                    print()
                elif ch == b"h":
                    help_str = (
                        "\nTo use the interactive terminal, press the following keys:\n"
                    )
                    # right align this strings on the colon
                    help_str += "\t     Enter: Update quotes\n"
                    help_str += "\t Backspace: Reset offset\n"
                    help_str += "\t  Up Arrow: Increase offset\n"
                    help_str += "\tDown Arrow: Decrease offset\n"
                    help_str += "\t         x: Cancel all orders\n"
                    help_str += "\t         q: Cancel all orders and exit program\n"
                    help_str += "\t         v: Print trader balances\n"
                    help_str += "\t         h: Print this help message\n"
                    print(help_str)

                # handle arrow keys
                if ch == b"\x1b":
                    prev = ch
                    continue
                elif prev == b"\x1b" and ch == b"[":
                    prev = ch
                    continue
                elif prev == b"[":
                    # handle up arrow
                    if ch == b"A":
                        self.offset_in_bps += 1
                        print(
                            f"Offset Up {self.offset_in_bps - 1} -> {self.offset_in_bps}"
                        )
                    # handle down arrow
                    elif ch == b"B":
                        self.offset_in_bps -= 1
                        print(
                            f"Offset Down {self.offset_in_bps + 1} -> {self.offset_in_bps}"
                        )
                    prev = None


@contextlib.contextmanager
def raw_mode(file):
    old_attrs = termios.tcgetattr(file.fileno())
    new_attrs = old_attrs[:]
    new_attrs[3] = new_attrs[3] & ~(termios.ECHO | termios.ICANON)
    try:
        termios.tcsetattr(file.fileno(), termios.TCSADRAIN, new_attrs)
        yield
    finally:
        termios.tcsetattr(file.fileno(), termios.TCSADRAIN, old_attrs)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keypair-path", type=str, help="Path to keypair")
    # Allow user to pass in keypair base58 string
    parser.add_argument("--keypair", type=str, help="Keypair base58 string")
    # Allow user to pass in url with -u or --url
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        help="URL of Solana cluster",
        default="https://api.mainnet-beta.solana.com",
    )
    # Allow user to specify edge in bps
    parser.add_argument(
        "-e",
        "--edge",
        type=int,
        help="Edge in basis points",
        default=5,
    )

    # Allow user to specify quote size in $
    parser.add_argument(
        "-q",
        "--quote-size",
        type=int,
        help="Quote size in $",
        default=20,
    )
    # Allow user to pass in `use_binance`
    parser.add_argument(
        "--use-binance",
        action="store_true",
        help="Use Binance instead of Coinbase",
        default=False,
    )

    args = parser.parse_args()

    if args.keypair is not None:
        signer = Keypair.from_base58_string(args.keypair)
    elif args.keypair_path is not None:
        expanded_path = os.path.expanduser(args.keypair_path)
        with open(expanded_path, "r") as file:
            byte_array = json.load(file)
        signer = Keypair.from_bytes(byte_array)
    else:
        raise Exception("Must provide keypair or keypair path")

    print("Pubkey", signer.pubkey())

    client = PhoenixClient(
        endpoint=args.url,
    )
    bot = Bot(
        signer,
        client,
        Pubkey.from_string("4DoNfFBfF7UokCC2FQzriy7yHK6DY6NVdYpuekQ5pRgg"),
        edge_in_basis_points=args.edge,
        quote_size=args.quote_size,
    )
    await bot.initialize()
    print("Press 'h' to see help message")
    if args.use_binance:
        await asyncio.gather(
            bot.get_usdc_usdt_price(),
            bot.get_fair_price_from_binance(),
            bot.l2_book_subscribe(),
            bot.market_subscribe(),
            bot.hearbeat(),
            bot.offset_subscribe(),
            bot.order_subscribe(),
        )
    else:
        await asyncio.gather(
            bot.get_fair_price_from_coinbase(),
            bot.l2_book_subscribe(),
            bot.market_subscribe(),
            bot.hearbeat(),
            bot.offset_subscribe(),
            bot.order_subscribe(),
        )


asyncio.run(main())
