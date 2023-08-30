import datetime
from typing import TypedDict, Union, List
from uuid import uuid4
from phoenix.instructions import cancel_all_orders
from phoenix.instructions import cancel_multiple_orders_by_id
from phoenix.instructions.cancel_all_orders import CancelAllOrdersAccounts
from phoenix.instructions.cancel_multiple_orders_by_id import (
    CancelMultipleOrdersByIdAccounts,
    CancelMultipleOrdersByIdArgs,
)
from phoenix.market_metadata import MarketMetadata
from phoenix.program_id import PROGRAM_ID
from phoenix.types import self_trade_behavior
from phoenix.types.cancel_multiple_orders_by_id_params import (
    CancelMultipleOrdersByIdParams,
)
from phoenix.types.cancel_order_params import CancelOrderParams
from phoenix.types.market_status import PostOnly
from phoenix.types.order_packet import (
    ImmediateOrCancel,
    Limit,
    LimitValue,
    OrderPacketKind,
)
from spl.token.instructions import get_associated_token_address
from phoenix.types.side import Ask, Bid, SideKind
from phoenix.events import get_phoenix_events_from_confirmed_transaction_with_meta
from solana.rpc.commitment import Commitment
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solders.pubkey import Pubkey
from solders.hash import Hash
from solana.transaction import Instruction, Transaction, Keypair
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
        market_pubkey: Pubkey,
        side: SideKind,
        price_in_quote_units: float,
        size_in_base_units: float,
        client_order_id: int = None,
        self_trade_behavior: self_trade_behavior = self_trade_behavior.DecrementTake,
        match_limit: int = None,
        use_only_deposit_funds: bool = False,
        last_valid_slot: int = None,
        last_valid_unix_timestamp: int = None,
        fail_silently_on_insufficient_funds: bool = False,
    ) -> ExecutableOrder:
        market_metadata: MarketMetadata = self.markets.get(market_pubkey, None)
        if market_metadata == None:
            raise ValueError("Market address not found: ", market_pubkey)

        if client_order_id is None:
            client_order_id = (
                uuid4().int
            )  # TODO: Replace with method to track orders from python client
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
            market_pubkey=market_pubkey,
        )

    def create_place_limit_order_instruction(
        self, limit_order_packet: Limit, market_pubkey: Pubkey, trader_pubkey: Pubkey
    ) -> Instruction:
        market_metadata: MarketMetadata = self.markets.get(market_pubkey, None)
        if market_metadata == None:
            raise ValueError("Market not found for order: ", limit_order_packet)
        return market_metadata.create_place_limit_order_instruction(
            limit_order_packet, trader_pubkey
        )

    # TODO: Make cancel order parameter the correct type and add support
    # TODO: Add support for other order types
    async def send_orders(
        self,
        signer: Keypair,
        order_packets: List[ExecutableOrder],
        pre_instructions: [Instruction] = None,
        post_instructions: [Instruction] = None,
        commitment=None,
        tx_opts: TxOpts | None = None,
        recent_blockhash: Hash | None = None,
    ):
        # Create instructions for each order_packet and create client_order_id map
        # Add instructions to transaction
        transaction = Transaction()

        # Add pre-instructions
        if pre_instructions is not None:
            for instruction in pre_instructions:
                transaction.add(instruction)

        client_orders_map: TypedDict[int, FIFOOrderId] = {}
        for executable_order in order_packets:
            order_packet = executable_order.order_packet
            market_pubkey = executable_order.market_pubkey
            match type(order_packet):
                case _ if isinstance(order_packet, Limit):
                    limit_order_instruction = self.create_place_limit_order_instruction(
                        order_packet, market_pubkey, signer.pubkey()
                    )
                    client_orders_map[order_packet.value["client_order_id"]] = None
                    transaction.add(limit_order_instruction)
                case _ if isinstance(order_packet, PostOnly):
                    raise ValueError("Unimplemented order type, PostOnly")
                case _ if isinstance(order_packet, ImmediateOrCancel):
                    raise ValueError("Unimplemented order type, ImmediateOrCancel")
                case _:
                    raise ValueError("Unrecognized order type")

        # Add pre-instructions
        if post_instructions is not None:
            for instruction in post_instructions:
                transaction.add(instruction)

        # Send transaction
        response = await self.client.send_transaction(
            transaction, signer, opts=tx_opts, recent_blockhash=recent_blockhash
        )
        signature = response.value
        # Get transaction and parse for the FIFOOrderId of each order
        commitment = commitment if commitment is not None else self.commitment
        await self.client.confirm_transaction(signature, commitment)
        transaction_response = await self.client.get_transaction(
            signature, "json", commitment
        )
        transaction = transaction_response.value
        phoenix_transaction = get_phoenix_events_from_confirmed_transaction_with_meta(
            transaction
        )
        for ix_events in phoenix_transaction.events_from_instructions:
            for phoenix_event in ix_events.events:
                if phoenix_event.kind == "Place":
                    client_orders_map[
                        phoenix_event.value[0].client_order_id
                    ] = FIFOOrderId(
                        phoenix_event.value[0].price_in_ticks,
                        phoenix_event.value[0].order_sequence_number,
                    )

        return client_orders_map

    def create_cancel_order_instruction(
        self,
        trader: Pubkey,
        market_pubkey: Pubkey,
        order_ids: Union[List[FIFOOrderId], None] = None,
    ) -> Instruction:
        log_account = Pubkey.find_program_address([b"log"], PROGRAM_ID)[0]
        market_metadata = self.markets.get(market_pubkey, None)
        if market_metadata == None:
            raise ValueError("Market not found: ", market_pubkey)
        if order_ids is None:
            accounts = CancelAllOrdersAccounts(
                phoenix_program=PROGRAM_ID,
                log_authority=log_account,
                market=market_pubkey,
                trader=trader,
                base_account=get_associated_token_address(
                    trader, market_metadata.base_mint
                ),
                quote_account=get_associated_token_address(
                    trader, market_metadata.quote_mint
                ),
                base_vault=market_metadata.base_vault,
                quote_vault=market_metadata.quote_vault,
            )
            return cancel_all_orders(accounts)
        else:
            accounts = CancelMultipleOrdersByIdAccounts(
                phoenix_program=PROGRAM_ID,
                log_authority=log_account,
                market=market_pubkey,
                trader=trader,
                base_account=get_associated_token_address(
                    trader, market_metadata.base_mint
                ),
                quote_account=get_associated_token_address(
                    trader, market_metadata.quote_mint
                ),
                base_vault=market_metadata.base_vault,
                quote_vault=market_metadata.quote_vault,
            )

            orders = [
                CancelOrderParams(
                    side=Bid if order_id.order_sequence_number >= 1 << 63 else Ask,
                    price_in_ticks=order_id.price_in_ticks,
                    order_sequence_number=order_id.order_sequence_number,
                )
                for order_id in order_ids
            ]
            args = CancelMultipleOrdersByIdArgs(
                params=CancelMultipleOrdersByIdParams(orders=orders)
            )
            return cancel_multiple_orders_by_id(args, accounts)

    async def cancel_orders(
        self,
        signer: Keypair,
        market_pubkey: Pubkey,
        order_ids: Union[List[FIFOOrderId], None] = None,
        commitment=None,
        tx_opts: TxOpts | None = None,
        recent_blockhash: Hash | None = None,
    ) -> [FIFOOrderId]:
        log_account = Pubkey.find_program_address([b"log"], PROGRAM_ID)[0]
        market_metadata = self.markets.get(market_pubkey, None)
        if market_metadata == None:
            raise ValueError("Market not found: ", market_pubkey)

        transaction = Transaction()
        transaction.add(
            self.create_cancel_order_instruction(
                signer.pubkey(), market_pubkey, order_ids
            )
        )
        # Get transaction and parse for the FIFOOrderId of each order
        commitment = commitment if commitment is not None else self.commitment
        # Send transaction
        response = await self.client.send_transaction(
            transaction, signer, opts=tx_opts, recent_blockhash=recent_blockhash
        )
        signature = response.value
        await self.client.confirm_transaction(signature, commitment)
        transaction_response = await self.client.get_transaction(
            signature, "json", commitment
        )
        transaction = transaction_response.value
        phoenix_transaction = get_phoenix_events_from_confirmed_transaction_with_meta(
            transaction
        )
        cancelled_orders: [FIFOOrderId] = []
        for ix_events in phoenix_transaction.events_from_instructions:
            for phoenix_event in ix_events.events:
                if phoenix_event.kind == "Reduce":
                    if phoenix_event.value[0].base_lots_remaining == 0:
                        cancelled_orders.append(
                            FIFOOrderId(
                                price_in_ticks=phoenix_event.value[0].price_in_ticks,
                                order_sequence_number=phoenix_event.value[
                                    0
                                ].order_sequence_number,
                            )
                        )
        return cancelled_orders
