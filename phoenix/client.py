import datetime
from uuid import uuid4
from construct import Optional
from phoenix.market_metadata import MarketMetadata
from phoenix.types import self_trade_behavior
from phoenix.types.order_packet import Limit, LimitValue, OrderPacketKind
from phoenix.types.side import SideKind
from solana.rpc.commitment import Commitment
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solders.pubkey import Pubkey
from solana.transaction import Instruction, Transaction, Keypair
import base64
from phoenix.types.fifo_order_id import FIFOOrderId


from .market import DEFAULT_L2_LADDER_DEPTH, Market


class ExecutableOrder:
    def __init__(
        self,
        order_packet: OrderPacketKind,
        market_pubkey: Pubkey,
    ):
        self.order_packet = order_packet
        self.market_pubkey = market_pubkey


class PhoenixClient:
    def __init__(
        self,
        endpoint="api.mainnet-beta.solana.com",
        custom_url=None,
        custom_ws_url=None,
        commitment: Commitment = "confirmed",
        encoding: str = "base64+zstd",
    ):
        if custom_url is None:
            self.endpoint = f"https://{endpoint.split('://')[-1]}"
        else:
            self.endpoint = custom_url
        self.client = AsyncClient(self.endpoint)

        if custom_ws_url is None:
            self.ws_endpoint = f"wss://{endpoint.split('://')[-1]}"
        else:
            self.ws_endpoint = custom_ws_url

        self.commitment = commitment
        self.encoding = encoding

        self.markets = {}

    async def add_market(self, market_pubkey: Pubkey):
        market_bytes = await self.client.get_account_info(
            market_pubkey, self.commitment, self.encoding
        )
        self.markets[market_pubkey] = Market.deserialize_market_data(
            market_pubkey, market_bytes.value.data
        ).metadata

    async def get_l2_book(self, market_pubkey: Pubkey, levels=DEFAULT_L2_LADDER_DEPTH):
        market_account = await self.client.get_account_info(
            market_pubkey, self.commitment, self.encoding
        )
        slot = market_account.context.slot
        market = Market.deserialize_market_data(
            market_pubkey, market_account.value.data
        )
        unix_timestamp = (await self.client.get_block_time(slot)).value
        return market.get_ui_ladder(slot, unix_timestamp, levels)

    async def close(self):
        await self.client.close()

    def get_limit_order_packet(
        self,
        side: SideKind,
        price_in_quote_units: float,
        size_in_base_units: float,
        market_metadata: MarketMetadata,
        client_order_id: int = None,
        self_trade_behavior: self_trade_behavior = self_trade_behavior.DecrementTake,
        match_limit: int = None,
        use_only_deposit_funds: bool = False,
        last_valid_slot: int = None,
        last_valid_unix_timestamp: int = None,
        fail_silently_on_insufficient_funds: bool = False,
    ) -> ExecutableOrder:
        if client_order_id is None:
            client_order_id = (
                uuid4().int
            )  # TODO: Replace with scheme to track orders from python client
        price_in_ticks = market_metadata.float_price_to_ticks_rounded_down(
            price_in_quote_units
        )
        num_base_lots = market_metadata.raw_base_units_to_base_lots_rounded_down(
            size_in_base_units
        )
        return ExecutableOrder(
            Limit(
                LimitValue(
                    side=side,
                    price_in_ticks=price_in_ticks,
                    num_base_lots=num_base_lots,
                    self_trade_behavior=self_trade_behavior,
                    match_limit=match_limit,
                    client_order_id=client_order_id,
                    use_only_deposited_funds=use_only_deposit_funds,
                    last_valid_slot=last_valid_slot,
                    last_valid_unix_timestamp_in_seconds=last_valid_unix_timestamp,
                    fail_silently_on_insufficient_funds=fail_silently_on_insufficient_funds,
                )
            ),
            market_metadata.address,
        )

    def get_place_limit_order_instruction(
        self, limit_order_packet: Limit, market_pubkey: Pubkey, trader_pubkey: Pubkey
    ) -> Instruction:
        market_metadata: MarketMetadata = self.markets.get(market_pubkey, None)
        if market_metadata == None:
            raise ValueError("Market not found for order: " + limit_order_packet)
        return market_metadata.create_place_limit_order_instruction(
            limit_order_packet, trader_pubkey
        )

    # TODO: Make cancel order parameter the correct type and add support
    # TODO: Keep track of client order ids and return them when order is complete
    async def execute(
        self,
        order_packets: [ExecutableOrder],
        signer: Keypair,
        cancel_orders: [int] = None,
        commitment=None,
    ):
        # Create instructiosn for each order_packet
        # Add instructions to transaction
        transaction = Transaction()
        for order in order_packets:
            if isinstance(order.order_packet, Limit):
                limit_order_instruction = self.get_place_limit_order_instruction(
                    order.order_packet, order.market_pubkey, signer.pubkey()
                )
                transaction.add(limit_order_instruction)
            else:
                raise ValueError("Unimplemented order type")

        # Send transaction
        commitment = commitment if commitment is not None else self.commitment
        response = await self.client.send_transaction(
            transaction,
            signer,
        )

        # TODO: Get instruction parsing logic from GPT and use it to get the order_sequence_number
        print(response)

        signature = response.value
        await self.client.confirm_transaction(signature, commitment)

        # Note: The return data of the transaction is not currently working since it only returns it for the last instruction executed
        # transaction = await self.client.get_transaction(signature, "json", commitment)
        # returned_data = transaction.value.transaction.meta.return_data
        # print(transaction.value.transaction.meta.return_data)

        # if returned_data is not None:
        #     data = returned_data.data

        #     # Parse the length prefix
        #     num_orders_from_prefix = int.from_bytes(data[:4], byteorder="little")
        #     data = data[4:]  # Remove the length prefix

        #     # Just for safety, check that the calculated number of orders from data length matches the prefix
        #     assert num_orders_from_prefix == len(data) // FIFOOrderId.size()

        #     order_sequence_numbers = []

        #     for i in range(num_orders_from_prefix):
        #         order_data = data[i * FIFOOrderId.size() : (i + 1) * FIFOOrderId.size()]
        #         order_container = FIFOOrderId.layout.parse(order_data)
        #         order_sequence_numbers.append(FIFOOrderId.from_decoded(order_container))

        #     # Print the list of orders
        #     for order in order_sequence_numbers:
        #         print(order.to_json())
