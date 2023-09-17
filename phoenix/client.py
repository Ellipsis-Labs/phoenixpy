import asyncio
import traceback
from dataclasses import dataclass
import base58
import json
from typing import Any, Callable, Dict, Iterator, Tuple, TypedDict, Union, List
from uuid import uuid4
import time
import traceback
from asyncstdlib import enumerate
import websockets
from phoenix.instructions import cancel_all_orders, withdraw_funds
from phoenix.instructions import cancel_multiple_orders_by_id
from phoenix.instructions import cancel_all_orders_with_free_funds
from phoenix.instructions import cancel_multiple_orders_by_id_with_free_funds
from phoenix.instructions.cancel_all_orders import CancelAllOrdersAccounts
from phoenix.instructions.cancel_all_orders_with_free_funds import (
    CancelAllOrdersWithFreeFundsAccounts,
)
from phoenix.instructions.cancel_multiple_orders_by_id import (
    CancelMultipleOrdersByIdAccounts,
    CancelMultipleOrdersByIdArgs,
)
from phoenix.instructions.withdraw_funds import (
    WithdrawFundsAccounts,
    WithdrawFundsArgs,
    withdraw_funds,
)
from phoenix.instructions.cancel_multiple_orders_by_id_with_free_funds import (
    CancelMultipleOrdersByIdWithFreeFundsAccounts,
    CancelMultipleOrdersByIdWithFreeFundsArgs,
)
from phoenix.market_metadata import MarketMetadata
from phoenix.order_subscribe_response import (
    CancelledOrder,
    FilledOrder,
    OpenOrder,
    OrderSubscribeError,
    OrderSubscribeResponse,
)
from phoenix.program_id import PROGRAM_ID
from phoenix.types import self_trade_behavior
from phoenix.types.cancel_multiple_orders_by_id_params import (
    CancelMultipleOrdersByIdParams,
)
from phoenix.types.cancel_order_params import CancelOrderParams
from phoenix.types.order_packet import (
    ImmediateOrCancel,
    ImmediateOrCancelValue,
    Limit,
    LimitValue,
    OrderPacketKind,
    PostOnly,
    PostOnlyValue,
)
from spl.token.instructions import get_associated_token_address
from phoenix.types.side import Ask, Bid, SideKind, from_order_sequence_number
from phoenix.events import (
    PhoenixTransaction,
    get_phoenix_events_from_confirmed_transaction_with_meta,
    get_phoenix_events_from_log_data,
)
from solana.rpc.commitment import Commitment
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solders.pubkey import Pubkey
from solders.hash import Hash
from solders.signature import Signature
from solders.rpc.config import RpcTransactionLogsFilterMentions
from solana.transaction import Instruction, Transaction, Keypair
from solana.rpc.websocket_api import connect
from phoenix.types.fifo_order_id import FIFOOrderId
from phoenix.types.withdraw_params import WithdrawParams
from jsonrpcclient import request

from .market import DEFAULT_L2_LADDER_DEPTH, Ladder, Market


class ExecutableOrder:
    def __init__(
        self,
        order_packet: OrderPacketKind,
        market_pubkey: Pubkey,
    ):
        self.order_packet = order_packet
        self.market_pubkey = market_pubkey


class PhoenixOrder:
    def __init__(
        self,
        order_id: FIFOOrderId,
        base_lots_remaining: int,
    ):
        self.order_id = order_id
        self.base_lots_remaining = base_lots_remaining

    def __repr__(self):
        return f"PhoenixOrder({self.order_id}, {self.base_lots_remaining})"


class PhoenixResponse:
    def __init__(
        self,
        signature: Signature,
        sequence_number: int,
        client_orders_map: Dict[int, PhoenixOrder],
        cancelled_orders: List[PhoenixOrder] = None,
    ):
        self.signature = signature
        self.sequence_number = sequence_number
        self.client_orders_map = client_orders_map
        if cancelled_orders is None:
            self.cancelled_orders = []
        else:
            self.cancelled_orders = cancelled_orders


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

        self.__slot = -1
        self.__subscribed_to_slot = False

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

    async def order_subscribe_with_default_client(
        self, market_pubkey: Pubkey, trader_pubkey: Pubkey
    ) -> Iterator[List[OrderSubscribeResponse]]:
        error_count = 0
        reconnection_count = 0
        while True:
            reconnection_count += 1
            async with connect(self.ws_endpoint) as websocket:
                await websocket.logs_subscribe(
                    commitment=self.commitment,
                    filter_=RpcTransactionLogsFilterMentions(PROGRAM_ID),
                )
                await websocket.recv()
                async for msg in websocket:
                    if msg[0].result.value.err != None:
                        continue
                    try:
                        sig = msg[0].result.value.signature
                        transaction = None
                        attempts = 0
                        while transaction is None and attempts < 5:
                            attempts += 1
                            tx_response = await self.client.get_transaction(
                                sig,
                                "json",
                                self.commitment,
                                max_supported_transaction_version=1,
                            )
                            transaction = tx_response.value
                        if transaction is None:
                            error_count += 1
                            yield (
                                [
                                    OrderSubscribeError(
                                        message=f"Transaction not found: {sig}",
                                        error_count=error_count,
                                        reconnection_count=reconnection_count,
                                        reconnected=False,
                                        traceback=None,
                                        exception=None,
                                    )
                                ]
                            )
                            continue
                        phoenix_transaction = (
                            get_phoenix_events_from_confirmed_transaction_with_meta(
                                transaction
                            )
                        )
                        response = self.__get_response_from_phoenix_transaction(
                            phoenix_transaction, market_pubkey, trader_pubkey
                        )
                        if len(response) > 0:
                            yield response
                    except websockets.exceptions.ConnectionClosed as e:
                        print("Connection closed unexpectedly. Reconnecting...")
                        err = OrderSubscribeError(
                            message="Websocked connection closed",
                            error_count=error_count,
                            reconnection_count=reconnection_count,
                            reconnected=True,
                            traceback=traceback.extract_stack(),
                            exception=e,
                        )
                        yield [err]
                        error_count += 1
                        break
                    except Exception as e:
                        err = OrderSubscribeError(
                            message=f"Error processing transaction event: {e}",
                            error_count=error_count,
                            reconnection_count=reconnection_count,
                            reconnected=False,
                            traceback=traceback.extract_stack(),
                            exception=e,
                        )
                        yield [err]
                        error_count += 1

    async def order_subscribe(
        self, market_pubkey: Pubkey, trader_pubkey: Pubkey
    ) -> Iterator[List[OrderSubscribeResponse]]:
        error_count = 0
        reconnection_count = 0
        while True:
            reconnection_count += 1
            async with websockets.connect(self.ws_endpoint + "/whirligig") as websocket:
                try:
                    transaction_subscribe = request(
                        "transactionSubscribe",
                        params=[
                            {
                                "mentions": [str(market_pubkey)],
                                "failed": False,
                                "vote": False,
                            },
                            {
                                "commitment": "confirmed",
                            },
                        ],
                    )
                    await websocket.send(json.dumps(transaction_subscribe))
                    # Ignore the first message
                    await websocket.recv()
                    while True:
                        try:
                            response = self.__process_transaction_event(
                                json.loads(await websocket.recv()),
                                market_pubkey,
                                trader_pubkey,
                            )
                            if len(response) > 0:
                                yield response
                        except websockets.exceptions.ConnectionClosed as e:
                            print("Connection closed unexpectedly. Reconnecting...")
                            err = OrderSubscribeError(
                                message="Websocked connection closed",
                                error_count=error_count,
                                reconnection_count=reconnection_count,
                                reconnected=True,
                                traceback=traceback.extract_stack(),
                                exception=e,
                            )
                            yield [err]
                            error_count += 1
                            break
                        except Exception as e:
                            err = OrderSubscribeError(
                                message=f"Error processing transaction event: {e}",
                                error_count=error_count,
                                reconnection_count=reconnection_count,
                                reconnected=False,
                                traceback=traceback.extract_stack(),
                                exception=e,
                            )
                            yield [err]
                            error_count += 1

                except Exception as e:
                    err = OrderSubscribeError(
                        message=f"Error processing transaction event: {e}",
                        error_count=error_count,
                        reconnection_count=reconnection_count,
                        reconnected=False,
                        traceback=traceback.extract_stack(),
                        exception=e,
                    )
                    yield [err]
                    error_count += 1

    def __process_transaction_event(
        self, response, market_pubkey: Pubkey, trader_pubkey: Pubkey
    ) -> [OrderSubscribeResponse]:
        payload = response["params"]["result"]["value"]
        meta = payload["meta"]
        loaded_addresses = meta.get("loadedAddresses", {"readonly": [], "writable": []})
        message = payload["transaction"]["message"][-1]
        base_account_keys = list(
            map(
                lambda l: Pubkey.from_bytes(bytes(l)),
                message["accountKeys"][1:],
            )
        )
        lookup_table_keys = list(
            map(
                Pubkey.from_string,
                loaded_addresses["writable"] + loaded_addresses["readonly"],
            )
        )
        account_keys = base_account_keys + lookup_table_keys
        data_array: List[bytes] = []
        for inner_ix in meta["innerInstructions"]:
            for ix in inner_ix["instructions"]:
                program = account_keys[ix["programIdIndex"]]
                if program != PROGRAM_ID:
                    continue
                data = base58.b58decode(ix["data"])
                if data[0] == 15:
                    data_array.append(data[1:])

        instructions = [get_phoenix_events_from_log_data(data) for data in data_array]

        phoenix_tx = PhoenixTransaction(
            instructions,
            signature=Signature.from_bytes(payload["transaction"]["signatures"][1]),
            txReceived=True,
            txFailed=False,
        )
        return self.__get_response_from_phoenix_transaction(
            phoenix_tx, market_pubkey=market_pubkey, trader_pubkey=trader_pubkey
        )

    def __get_response_from_phoenix_transaction(
        self, phoenix_tx, market_pubkey, trader_pubkey
    ):
        response = []
        for event in phoenix_tx.events_from_instructions:
            header = event.header
            if header.market != market_pubkey:
                continue
            for e in event.events:
                if e.kind == "Fill":
                    fill = e.value[0]
                    if fill.maker_id == trader_pubkey:
                        filled_order = FilledOrder(
                            order_id=FIFOOrderId(
                                order_sequence_number=fill.order_sequence_number,
                                price_in_ticks=fill.price_in_ticks,
                            ),
                            market_pubkey=market_pubkey,
                            slot=header.slot,
                            unix_timestamp_in_seconds=header.timestamp,
                            sequence_number=header.sequence_number,
                            taker_side=from_order_sequence_number(
                                fill.order_sequence_number
                            ).opposite(),
                            base_lots_filled=fill.base_lots_filled,
                            base_lots_remaining=fill.base_lots_remaining,
                            taker_pubkey=header.signer,
                            maker_pubkey=fill.maker_id,
                        )
                        response.append(filled_order)
                elif e.kind == "Place":
                    place = e.value[0]
                    if header.signer == trader_pubkey:
                        open_order = OpenOrder(
                            order_id=FIFOOrderId(
                                order_sequence_number=place.order_sequence_number,
                                price_in_ticks=place.price_in_ticks,
                            ),
                            market_pubkey=market_pubkey,
                            slot=header.slot,
                            unix_timestamp_in_seconds=header.timestamp,
                            sequence_number=header.sequence_number,
                            side=from_order_sequence_number(
                                place.order_sequence_number
                            ),
                            base_lots_placed=place.base_lots_placed,
                            maker_pubkey=trader_pubkey,
                        )
                        response.append(open_order)
                elif e.kind == "Reduce":
                    reduce = e.value[0]
                    if header.signer == trader_pubkey:
                        cancelled_order = CancelledOrder(
                            order_id=FIFOOrderId(
                                order_sequence_number=reduce.order_sequence_number,
                                price_in_ticks=reduce.price_in_ticks,
                            ),
                            market_pubkey=market_pubkey,
                            slot=header.slot,
                            unix_timestamp_in_seconds=header.timestamp,
                            sequence_number=header.sequence_number,
                            side=from_order_sequence_number(
                                reduce.order_sequence_number
                            ),
                            base_lots_removed=reduce.base_lots_removed,
                            base_lots_remaining=reduce.base_lots_remaining,
                            maker_pubkey=trader_pubkey,
                        )
                        response.append(cancelled_order)
                elif e.kind == "ExpiredOrder":
                    expired = e.value[0]
                    if header.signer == trader_pubkey:
                        cancelled_order = CancelledOrder(
                            order_id=FIFOOrderId(
                                order_sequence_number=expired.order_sequence_number,
                                price_in_ticks=expired.price_in_ticks,
                            ),
                            market_pubkey=market_pubkey,
                            slot=header.slot,
                            unix_timestamp_in_seconds=header.timestamp,
                            sequence_number=header.sequence_number,
                            side=from_order_sequence_number(
                                expired.order_sequence_number
                            ),
                            base_lots_removed=expired.base_lots_removed,
                            base_lots_remaining=0,
                            maker_pubkey=trader_pubkey,
                        )
                        response.append(cancelled_order)
                elif e.kind == "Evict":
                    evicted = e.value[0]
                    if header.signer == trader_pubkey:
                        cancelled_order = CancelledOrder(
                            order_id=FIFOOrderId(
                                order_sequence_number=evicted.order_sequence_number,
                                price_in_ticks=evicted.price_in_ticks,
                            ),
                            market_pubkey=market_pubkey,
                            slot=header.slot,
                            unix_timestamp_in_seconds=header.timestamp,
                            sequence_number=header.sequence_number,
                            side=from_order_sequence_number(
                                evicted.order_sequence_number
                            ),
                            base_lots_removed=evicted.base_lots_evicted,
                            base_lots_remaining=0,
                            maker_pubkey=trader_pubkey,
                        )
                        response.append(cancelled_order)
        return response

    async def market_subscribe(
        self, market_pubkey: Pubkey, handle_market: Callable[[Market], Any]
    ):
        await asyncio.gather(
            self.__slot_subscribe(),
            self.__market_subscribe(market_pubkey, handle_market),
        )

    async def l2_orderbook_subscribe(
        self,
        market_pubkey: Pubkey,
        handle_l2_orderbook: Callable[[Ladder], Any],
        depth=DEFAULT_L2_LADDER_DEPTH,
    ):
        async def handle_market(market: Market):
            ladder = market.get_ui_ladder(
                slot=self.__slot, unix_timestamp=int(time.time()), levels=depth
            )
            await handle_l2_orderbook(ladder)

        await self.market_subscribe(market_pubkey, handle_market)

    async def __market_subscribe(
        self, market_pubkey: Pubkey, handle_market: Callable[[Market], Any]
    ):
        async with connect(self.ws_endpoint) as websocket:
            await websocket.account_subscribe(
                market_pubkey, self.commitment, self.encoding
            )
            first_resp = await websocket.recv()
            subscription_id = first_resp[0].result
            async for _, msg in enumerate(websocket):
                try:
                    market = Market.deserialize_market_data(
                        market_pubkey, msg[0].result.value.data
                    )
                    await handle_market(market)
                except Exception as e:
                    print(f"WARNING: Failed to parse message in market subscribe: {e}")
                    print(traceback.format_exc())

            await websocket.account_unsubscribe(subscription_id)

    async def __slot_subscribe(self):
        if self.__subscribed_to_slot:
            return
        self.__subscribed_to_slot = True
        print("Subscribing to slot")
        async with connect(self.ws_endpoint) as websocket:
            await websocket.slot_subscribe()
            first_resp = await websocket.recv()
            subscription_id = first_resp[0].result
            async for _, msg in enumerate(websocket):
                try:
                    self.slot = msg[0].result.slot
                except Exception as e:
                    print(f"WARNING: Failed to parse message: {e}")
            await websocket.slot_unsubscribe(subscription_id)
        self.__subscribed_to_slot = False

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
        use_only_deposited_funds: bool = False,
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
                    use_only_deposited_funds=use_only_deposited_funds,
                    last_valid_slot=last_valid_slot,
                    last_valid_unix_timestamp_in_seconds=last_valid_unix_timestamp,
                    fail_silently_on_insufficient_funds=fail_silently_on_insufficient_funds,
                )
            ),
            market_pubkey=market_pubkey,
        )

    def get_post_only_order_packet(
        self,
        market_pubkey: Pubkey,
        side: SideKind,
        price_in_quote_units: float,
        size_in_base_units: float,
        client_order_id: int = None,
        reject_post_only: bool = False,
        use_only_deposited_funds: bool = False,
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
            PostOnly(
                PostOnlyValue(
                    side=side,
                    price_in_ticks=price_in_ticks,
                    num_base_lots=num_base_lots,
                    client_order_id=client_order_id,
                    reject_post_only=reject_post_only,
                    use_only_deposited_funds=use_only_deposited_funds,
                    last_valid_slot=last_valid_slot,
                    last_valid_unix_timestamp_in_seconds=last_valid_unix_timestamp,
                    fail_silently_on_insufficient_funds=fail_silently_on_insufficient_funds,
                )
            ),
            market_pubkey=market_pubkey,
        )

    def get_ioc_packet(
        self,
        market_pubkey: Pubkey,
        side: SideKind,
        size_in_base_units: float,
        size_in_quote_units: float = 0,
        min_base_units_to_fill: float = 0,
        min_quote_units_to_fill: float = 0,
        price_in_quote_units: float | None = None,
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

        price_in_ticks = None
        if price_in_quote_units is not None:
            price_in_ticks = market_metadata.float_price_to_ticks_rounded_down(
                price_in_quote_units
            )

        num_base_lots = market_metadata.raw_base_units_to_base_lots_rounded_down(
            size_in_base_units
        )
        num_quote_lots = market_metadata.quote_units_to_quote_lots(size_in_quote_units)
        min_base_lots_to_fill = (
            market_metadata.raw_base_units_to_base_lots_rounded_down(
                min_base_units_to_fill
            )
        )
        min_quote_lots_to_fill = market_metadata.quote_units_to_quote_lots(
            min_quote_units_to_fill
        )

        return ExecutableOrder(
            ImmediateOrCancel(
                ImmediateOrCancelValue(
                    side=side,
                    price_in_ticks=price_in_ticks,
                    num_base_lots=num_base_lots,
                    num_quote_lots=num_quote_lots,
                    min_base_lots_to_fill=min_base_lots_to_fill,
                    min_quote_lots_to_fill=min_quote_lots_to_fill,
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
        self,
        limit_order_packet: Union[Limit, PostOnly],
        market_pubkey: Pubkey,
        trader_pubkey: Pubkey,
    ) -> Instruction:
        market_metadata: MarketMetadata = self.markets.get(market_pubkey, None)
        if market_metadata == None:
            raise ValueError("Market not found for order: ", limit_order_packet)
        return market_metadata.create_place_limit_order_instruction(
            limit_order_packet, trader_pubkey
        )

    def create_swap_instruction(
        self,
        ioc_order_packet: ImmediateOrCancel,
        market_pubkey: Pubkey,
        trader_pubkey: Pubkey,
    ) -> Instruction:
        market_metadata: MarketMetadata = self.markets.get(market_pubkey, None)
        if market_metadata == None:
            raise ValueError("Market not found for order: ", ioc_order_packet)
        return market_metadata.create_swap_instruction(ioc_order_packet, trader_pubkey)

    async def send_orders(
        self,
        signer: Keypair,
        order_packets: List[ExecutableOrder],
        pre_instructions: [Instruction] = None,
        post_instructions: [Instruction] = None,
        commitment=None,
        tx_opts: TxOpts | None = None,
        recent_blockhash: Hash | None = None,
    ) -> PhoenixResponse | None:
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
            if isinstance(order_packet, Limit) or isinstance(order_packet, PostOnly):
                limit_order_instruction = self.create_place_limit_order_instruction(
                    order_packet, market_pubkey, signer.pubkey()
                )
                client_orders_map[order_packet.value["client_order_id"]] = None
                transaction.add(limit_order_instruction)
            elif isinstance(order_packet, ImmediateOrCancel):
                swap_instruction = self.create_swap_instruction(
                    order_packet, market_pubkey, signer.pubkey()
                )
                transaction.add(swap_instruction)
            else:
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
            signature, "json", commitment, 0
        )

        transaction = transaction_response.value
        if transaction is None:
            print("Failed to confirm transaction: ", signature)
            return None

        phoenix_transaction = get_phoenix_events_from_confirmed_transaction_with_meta(
            transaction
        )
        cancelled_orders = []
        sequence_number = -1
        for ix_events in phoenix_transaction.events_from_instructions:
            sequence_number = ix_events.header.sequence_number
            for phoenix_event in ix_events.events:
                if phoenix_event.kind == "Place":
                    client_orders_map[
                        phoenix_event.value[0].client_order_id
                    ] = PhoenixOrder(
                        FIFOOrderId(
                            phoenix_event.value[0].price_in_ticks,
                            phoenix_event.value[0].order_sequence_number,
                        ),
                        phoenix_event.value[0].base_lots_placed,
                    )
                if phoenix_event.kind == "Reduce":
                    cancelled_orders.append(
                        PhoenixOrder(
                            FIFOOrderId(
                                price_in_ticks=phoenix_event.value[0].price_in_ticks,
                                order_sequence_number=phoenix_event.value[
                                    0
                                ].order_sequence_number,
                            ),
                            phoenix_event.value[0].base_lots_remaining,
                        )
                    )
        return PhoenixResponse(
            signature=signature,
            # We add 1 because the sequence number is the sequence number of the last event in the transaction
            # The current market sequence number will have been incremented
            sequence_number=sequence_number + 1,
            client_orders_map=client_orders_map,
            cancelled_orders=cancelled_orders,
        )

    def create_cancel_order_instruction(
        self,
        trader: Pubkey,
        market_pubkey: Pubkey,
        order_ids: Union[List[FIFOOrderId], None] = None,
        withdraw_funds=True,
    ) -> Instruction:
        log_account = Pubkey.find_program_address([b"log"], PROGRAM_ID)[0]
        market_metadata = self.markets.get(market_pubkey, None)
        if market_metadata == None:
            raise ValueError("Market not found: ", market_pubkey)
        if order_ids is None:
            if withdraw_funds:
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
                accounts = CancelAllOrdersWithFreeFundsAccounts(
                    phoenix_program=PROGRAM_ID,
                    log_authority=log_account,
                    market=market_pubkey,
                    trader=trader,
                )
                return cancel_all_orders_with_free_funds(accounts)

        else:
            orders = [
                CancelOrderParams(
                    side=Bid if (order_id.order_sequence_number & 1 << 63 > 0) else Ask,
                    price_in_ticks=order_id.price_in_ticks,
                    order_sequence_number=order_id.order_sequence_number,
                )
                for order_id in order_ids
            ]
            if withdraw_funds:
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

                args = CancelMultipleOrdersByIdArgs(
                    params=CancelMultipleOrdersByIdParams(orders=orders)
                )
                return cancel_multiple_orders_by_id(args, accounts)
            else:
                accounts = CancelMultipleOrdersByIdWithFreeFundsAccounts(
                    phoenix_program=PROGRAM_ID,
                    log_authority=log_account,
                    market=market_pubkey,
                    trader=trader,
                )
                args = CancelMultipleOrdersByIdWithFreeFundsArgs(
                    params=CancelMultipleOrdersByIdParams(orders=orders)
                )
                return cancel_multiple_orders_by_id_with_free_funds(args, accounts)

    async def cancel_orders(
        self,
        signer: Keypair,
        market_pubkey: Pubkey,
        order_ids: Union[List[FIFOOrderId], None] = None,
        withdraw_cancelled_funds=True,
        withdraw_free_funds=False,
        commitment=None,
        tx_opts: TxOpts | None = None,
        recent_blockhash: Hash | None = None,
    ) -> Tuple[Signature, List[FIFOOrderId]]:
        market_metadata = self.markets.get(market_pubkey, None)
        if market_metadata == None:
            raise ValueError("Market not found: ", market_pubkey)

        transaction = Transaction()
        transaction.add(
            self.create_cancel_order_instruction(
                signer.pubkey(),
                market_pubkey,
                order_ids,
                withdraw_funds=withdraw_cancelled_funds,
            )
        )
        if withdraw_free_funds:
            args = WithdrawFundsArgs(
                withdraw_funds_params=WithdrawParams(
                    quote_lots_to_withdraw=None,
                    base_lots_to_withdraw=None,
                )
            )
            accounts = WithdrawFundsAccounts(
                phoenix_program=PROGRAM_ID,
                log_authority=Pubkey.find_program_address([b"log"], PROGRAM_ID)[0],
                market=market_pubkey,
                trader=signer.pubkey(),
                base_account=get_associated_token_address(
                    signer.pubkey(), market_metadata.base_mint
                ),
                quote_account=get_associated_token_address(
                    signer.pubkey(), market_metadata.quote_mint
                ),
                base_vault=market_metadata.base_vault,
                quote_vault=market_metadata.quote_vault,
            )
            transaction.add(withdraw_funds(args, accounts))
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
        return (signature, cancelled_orders)
