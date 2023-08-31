import contextlib
import sys
import termios
import argparse
import asyncio
import json
from typing import Union
import websockets
from solana.rpc.websocket_api import connect
from solana.rpc.types import TxOpts
from spl.token.instructions import (
    create_associated_token_account,
    get_associated_token_address,
)
from spl.token.constants import TOKEN_PROGRAM_ID, WRAPPED_SOL_MINT
from asyncstdlib import enumerate
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
from phoenix.types.side import Ask, Bid

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

        self.coinbase_vwap = None
        self.phoenix_best_bid = None
        self.phoenix_best_bid_size = None
        self.phoenix_best_ask = None
        self.phoenix_best_ask_size = None
        self.initialized = False
        self.sequence_number = -1
        self.metadata: Union[MarketMetadata, None] = None

        self.offset = 0

        self.__updating_quotes = False

    async def initialize(self):
        await self.phoenix_client.add_market(self.market)
        self.initialized = True
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

            balance = await self.phoenix_client.client.get_balance(
                sol_ata, commitment="confirmed"
            )

            if balance.value < 1e9:
                transaction = Transaction()
                # Top up the WSOL account with SOL and keep 1 SOL for gas
                transfer_ix = transfer(
                    TransferParams(
                        from_pubkey=self.signer.pubkey(),
                        to_pubkey=sol_ata,
                        lamports=int(wallet_balance - 1e9),
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

    async def get_fair_price(self):
        if not self.initialized:
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
                        "channels": [{"name": "ticker", "product_ids": ["SOL-USD"]}],
                    }
                )
            )
            while self.is_running:
                try:
                    data = await ws.recv()
                    if data != "":
                        price_feed = json.loads(data)
                        best_bid = float(price_feed["best_bid"])
                        best_ask = float(price_feed["best_ask"])
                        best_bid_size = float(price_feed["best_bid_size"])
                        best_ask_size = float(price_feed["best_ask_size"])
                        self.coinbase_vwap = (
                            best_bid * best_ask_size + best_ask * best_bid_size
                        ) / (best_bid_size + best_ask_size)
                        print(self.coinbase_vwap)
                        await self.update_quotes()
                    else:
                        print("Received empty message")
                except ValueError as e:
                    print(e)
                except Exception as e:
                    print(e)

    async def update_quotes(self, attempts=1):
        if attempts > 3:
            print("Failed to update quotes, attempted 3 times")
            self.__updating_quotes = False
            return
        self.__updating_quotes = True
        starting_orders = []
        starting_orders.extend(self.bids)
        starting_orders.extend(self.asks)

        fair = self.coinbase_vwap
        fair += self.metadata.ticks_to_float_price(self.offset)

        bid_price = fair * (1 - (self.edge_in_basis_points / 10000))
        bid = self.phoenix_client.get_limit_order_packet(
            self.market,
            Bid,
            bid_price,
            self.quote_size / bid_price,
            client_order_id=BID_CLIENT_ORDER_ID,
            fail_silently_on_insufficient_funds=True,
        )
        ask_price = fair * (1 + (self.edge_in_basis_points / 10000))
        ask = self.phoenix_client.get_limit_order_packet(
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
        print(response.sequence_number, response.signature)
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
                self.bids[0].order_id.price_in_ticks
            )
            placed_bid_size = self.metadata.base_lots_to_raw_base_units_as_float(
                self.bids[0].base_lots_remaining
            )

        placed_ask_price = None
        placed_ask_size = None
        if len(self.asks) > 0:
            placed_ask_price = self.metadata.ticks_to_float_price(
                self.asks[0].order_id.price_in_ticks
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

    async def handle_l2_orderbook(self, book: Ladder):
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
        if market.sequence_number <= self.sequence_number:
            return
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
            for order in market.bids:
                if order[1].trader_index != trader_index:
                    continue
                if order[0].order_sequence_number == bid.order_id.order_sequence_number:
                    found_bid = True
                    break
            if not found_bid:
                self.bids = []
                print(
                    (
                        market.sequence_number,
                        "SELL",
                        self.metadata.ticks_to_float_price(bid.order_id.price_in_ticks),
                        self.metadata.base_lots_to_raw_base_units_as_float(
                            bid.base_lots_remaining
                        ),
                    )
                )
        if len(self.asks) > 0:
            ask = self.asks[0]
            for order in market.asks:
                if order[1].trader_index != trader_index:
                    continue
                if order[0].order_sequence_number == ask.order_id.order_sequence_number:
                    found_ask = True
                    break
            if not found_ask:
                self.asks = []
                print(
                    (
                        market.sequence_number,
                        "BUY",
                        self.metadata.ticks_to_float_price(ask.order_id.price_in_ticks),
                        self.metadata.base_lots_to_raw_base_units_as_float(
                            ask.base_lots_remaining
                        ),
                    )
                )

        if not found_bid or not found_ask:
            await self.update_quotes()

    async def l2_book_subscribe(self):
        if not self.initialized:
            raise Exception("Bot not initialized")
        await self.phoenix_client.l2_orderbook_subscribe(
            self.market, self.handle_l2_orderbook
        )

    async def market_subscribe(self):
        if not self.initialized:
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
                    await self.update_quotes()
                # handle backspace key
                elif ch == b"\x7f":
                    prev = None
                    print(
                        f"Offset Reset {self.metadata.ticks_to_float_price(self.offset)} -> 0"
                    )
                    self.offset = 0
                    await self.update_quotes()

                print(f"Got key: {ch}")
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
                        self.offset += 1
                        print(
                            f"Offset Up {self.metadata.ticks_to_float_price(self.offset - 1)} -> {self.metadata.ticks_to_float_price(self.offset)}"
                        )
                    # handle down arrow
                    elif ch == b"B":
                        self.offset -= 1
                        print(
                            f"Offset Down {self.metadata.ticks_to_float_price(self.offset + 1)} -> {self.metadata.ticks_to_float_price(self.offset)}"
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
        edge_in_basis_points=5,
    )
    await bot.initialize()
    await asyncio.gather(
        bot.get_fair_price(),
        bot.l2_book_subscribe(),
        bot.market_subscribe(),
        bot.offset_subscribe(),
    )


asyncio.run(main())
