from typing import List, Tuple, Set, Any
import struct

from typing import List, Tuple, Dict

from solders.pubkey import Pubkey
from .market_metadata import MarketMetadata
from .types.market_header import MARKET_HEADER_SIZE, MarketHeader
from .types.fifo_order_id import FIFOOrderId
from .types.fifo_resting_order import FIFORestingOrder
from .types.trader_state import TraderState
from dataclasses import dataclass
from decimal import Decimal

DEFAULT_L2_LADDER_DEPTH = 10


class LadderLevel:
    price_in_ticks: Decimal
    size_in_base_lots: Decimal

    def __init__(self, price_in_ticks, size_in_base_lots):
        self.price_in_ticks = price_in_ticks
        self.size_in_base_lots = size_in_base_lots


class Ladder:
    bids: List[LadderLevel]
    asks: List[LadderLevel]

    def __init__(self):
        self.bids = []
        self.asks = []


class UiLadderLevel:
    price: Decimal
    size: Decimal

    def __init__(self, price, size):
        self.price = price
        self.size = size

    def __repr__(self) -> str:
        return f"{self.price} {self.size}"


class UiLadder:
    bids: List[UiLadderLevel]
    asks: List[UiLadderLevel]

    def __init__(self):
        self.bids = []
        self.asks = []

    def __repr__(self) -> str:
        ladder_str = ""
        for ask in reversed(self.asks):
            ladder_str += repr(ask)
            ladder_str += "\n"
        ladder_str += "\n"
        for bid in self.bids:
            ladder_str += repr(bid)
            ladder_str += "\n"
        return ladder_str


@dataclass
class Market:
    address: Pubkey
    metadata: MarketMetadata
    sequence_number: int
    base_lots_per_base_unit: int
    quote_lots_per_base_unit_per_tick: int
    order_sequence_number: int
    taker_fee_bps: int
    collected_quote_lot_fees: int
    unclaimed_quote_lot_fees: int
    bids: List[Tuple[FIFOOrderId, FIFORestingOrder]]
    asks: List[Tuple[FIFOOrderId, FIFORestingOrder]]
    traders: Dict[Pubkey, TraderState]
    trader_pubkey_to_trader_index: Dict[Pubkey, int]
    trader_index_to_trader_pubkey: Dict[int, Pubkey]

    @classmethod
    def deserialize_market_data(cls, market_pubkey: Pubkey, data: bytes) -> "Market":
        # Deserialize the market header

        header = MarketHeader.from_decoded(
            MarketHeader.layout.parse(data[:MARKET_HEADER_SIZE])
        )
        metadata = MarketMetadata(market_pubkey, header)
        offset = MARKET_HEADER_SIZE

        # Parse market data
        padding_len = 8 * 32
        remaining = data[offset + padding_len :]
        offset = 0

        base_lots_per_base_unit = int.from_bytes(
            remaining[offset : offset + 8], "little"
        )
        offset += 8
        quote_lots_per_base_unit_per_tick = int.from_bytes(
            remaining[offset : offset + 8], "little"
        )
        offset += 8
        sequence_number = int.from_bytes(remaining[offset : offset + 8], "little")
        offset += 8
        taker_fee_bps = int.from_bytes(remaining[offset : offset + 8], "little")
        offset += 8
        collected_quote_lot_fees = int.from_bytes(
            remaining[offset : offset + 8], "little"
        )
        offset += 8
        unclaimed_quote_lot_fees = int.from_bytes(
            remaining[offset : offset + 8], "little"
        )
        offset += 8
        remaining = remaining[offset:]

        # Parse bids, asks, and traders
        num_bids = header.market_size_params.bids_size
        num_asks = header.market_size_params.asks_size
        num_traders = header.market_size_params.num_seats

        bids_size = (
            16 + 16 + (16 + FIFOOrderId.size() + FIFORestingOrder.size()) * num_bids
        )
        asks_size = (
            16 + 16 + (16 + FIFOOrderId.size() + FIFORestingOrder.size()) * num_asks
        )
        traders_size = 16 + 16 + (16 + 32 + TraderState.size()) * num_traders
        offset = 0

        bid_buffer = remaining[offset : offset + bids_size]
        offset += bids_size
        ask_buffer = remaining[offset : offset + asks_size]
        offset += asks_size
        trader_buffer = remaining[offset : offset + traders_size]

        deserialize_fifo_order_id = lambda data, offset: FIFOOrderId.from_decoded(
            FIFOOrderId.layout.parse(data[offset : offset + FIFOOrderId.size()])
        )
        deserialize_fifo_resting_order = (
            lambda data, offset: FIFORestingOrder.from_decoded(
                FIFORestingOrder.layout.parse(
                    data[offset : offset + FIFORestingOrder.size()]
                )
            )
        )
        deserialize_pubkey = lambda data, offset: Pubkey(data[offset : offset + 32])
        deserialize_trader_state = lambda data, offset: TraderState.from_decoded(
            TraderState.layout.parse(data[offset : offset + TraderState.size()])
        )

        bids_unsorted = deserialize_red_black_tree(
            bid_buffer,
            FIFOOrderId.size(),
            FIFORestingOrder.size(),
            deserialize_fifo_order_id,
            deserialize_fifo_resting_order,
        )
        asks_unsorted = deserialize_red_black_tree(
            ask_buffer,
            FIFOOrderId.size(),
            FIFORestingOrder.size(),
            deserialize_fifo_order_id,
            deserialize_fifo_resting_order,
        )

        # Sort bids in descending order of price, and ascending order of sequence number
        bids = sorted(
            bids_unsorted,
            key=lambda x: (x[0].price_in_ticks, x[0].order_sequence_number),
            reverse=True,
        )

        # Sort asks in ascending order of price, and ascending order of sequence number
        asks = sorted(
            asks_unsorted,
            key=lambda x: (x[0].price_in_ticks, x[0].order_sequence_number),
        )

        traders = {}
        for k, trader_state in deserialize_red_black_tree(
            trader_buffer,
            32,
            TraderState.size(),
            deserialize_pubkey,
            deserialize_trader_state,
        ):
            traders[k] = trader_state

        trader_pubkey_to_trader_index = {}
        trader_index_to_trader_pubkey = {}
        for k, index in get_node_indices(
            trader_buffer,
            32,
            TraderState.size(),
            deserialize_pubkey,
            deserialize_trader_state,
        ).items():
            trader_pubkey_to_trader_index[k] = index
            trader_index_to_trader_pubkey[index] = k

        return cls(
            address=market_pubkey,
            metadata=metadata,
            sequence_number=header.market_sequence_number,
            base_lots_per_base_unit=base_lots_per_base_unit,
            quote_lots_per_base_unit_per_tick=quote_lots_per_base_unit_per_tick,
            order_sequence_number=sequence_number,
            taker_fee_bps=taker_fee_bps,
            collected_quote_lot_fees=collected_quote_lot_fees,
            unclaimed_quote_lot_fees=unclaimed_quote_lot_fees,
            bids=bids,
            asks=asks,
            traders=traders,
            trader_pubkey_to_trader_index=trader_pubkey_to_trader_index,
            trader_index_to_trader_pubkey=trader_index_to_trader_pubkey,
        )

    def get_bids(self, levels=1):
        return list(
            map(
                lambda order: (
                    self.metadata.ticks_to_float_price(order[0].price_in_ticks),
                    self.metadata.base_lots_to_raw_base_units_as_float(
                        order[1].num_base_lots
                    ),
                ),
                self.bids[:levels],
            )
        )

    def get_asks(self, levels=1):
        return list(
            map(
                lambda order: (
                    self.metadata.ticks_to_float_price(order[0].price_in_ticks),
                    self.metadata.base_lots_to_raw_base_units_as_float(
                        order[1].num_base_lots
                    ),
                ),
                self.asks[:levels],
            )
        )

    def get_ladder(
        self,
        slot: int = -1,
        unix_timestamp: int = -1,
        levels: int = DEFAULT_L2_LADDER_DEPTH,
    ) -> Ladder:
        ladder = Ladder()

        for order_id, resting_order in self.bids:
            if (
                resting_order.last_valid_slot != 0
                and resting_order.last_valid_slot < slot
            ):
                continue
            if (
                resting_order.last_valid_unix_timestamp_in_seconds != 0
                and resting_order.last_valid_unix_timestamp_in_seconds < unix_timestamp
            ):
                continue

            price_in_ticks = Decimal(order_id.price_in_ticks)
            size_in_base_lots = Decimal(resting_order.num_base_lots)
            if not ladder.bids:
                ladder.bids.append(LadderLevel(price_in_ticks, size_in_base_lots))
            else:
                prev = ladder.bids[-1]
                if price_in_ticks == prev.price_in_ticks:
                    prev.size_in_base_lots += size_in_base_lots
                else:
                    if len(ladder.bids) == levels:
                        break
                    ladder.bids.append(LadderLevel(price_in_ticks, size_in_base_lots))

        for order_id, resting_order in self.asks:
            if (
                resting_order.last_valid_slot != 0
                and resting_order.last_valid_slot < slot
            ):
                continue
            if (
                resting_order.last_valid_unix_timestamp_in_seconds != 0
                and resting_order.last_valid_unix_timestamp_in_seconds < unix_timestamp
            ):
                continue

            price_in_ticks = Decimal(order_id.price_in_ticks)
            size_in_base_lots = Decimal(resting_order.num_base_lots)
            if not ladder.asks:
                ladder.asks.append(LadderLevel(price_in_ticks, size_in_base_lots))
            else:
                prev = ladder.asks[-1]
                if price_in_ticks == prev.price_in_ticks:
                    prev.size_in_base_lots += size_in_base_lots
                else:
                    if len(ladder.asks) == levels:
                        break
                    ladder.asks.append(LadderLevel(price_in_ticks, size_in_base_lots))

        return ladder

    def get_ui_ladder(
        self,
        slot: int = -1,
        unix_timestamp: int = -1,
        levels: int = DEFAULT_L2_LADDER_DEPTH,
    ) -> UiLadder:
        ui_ladder = UiLadder()
        ladder = self.get_ladder(slot, unix_timestamp, levels)
        for bid in ladder.bids:
            ui_ladder.bids.append(
                UiLadderLevel(
                    Decimal(self.metadata.ticks_to_float_price(bid.price_in_ticks)),
                    Decimal(
                        self.metadata.base_lots_to_raw_base_units_as_float(
                            bid.size_in_base_lots
                        )
                    ),
                )
            )
        for ask in ladder.asks:
            ui_ladder.asks.append(
                UiLadderLevel(
                    Decimal(self.metadata.ticks_to_float_price(ask.price_in_ticks)),
                    Decimal(
                        self.metadata.base_lots_to_raw_base_units_as_float(
                            ask.size_in_base_lots
                        )
                    ),
                )
            )
        return ui_ladder


def deserialize_red_black_tree(
    data: bytes,
    key_size: int,
    value_size: int,
    deserialize_key,
    deserialize_value,
) -> list:
    tree_nodes = []
    nodes, free_nodes = deserialize_red_black_tree_nodes(
        data, key_size, value_size, deserialize_key, deserialize_value
    )

    for index, (key, value) in enumerate(nodes):
        if index not in free_nodes:
            tree_nodes.append((key, value))

    return tree_nodes


def get_node_indices(
    data: bytes,
    key_size: int,
    value_size: int,
    deserialize_key,
    deserialize_value,
) -> dict:
    index_map = {}
    nodes, free_nodes = deserialize_red_black_tree_nodes(
        data, key_size, value_size, deserialize_key, deserialize_value
    )

    for index, (key, _) in enumerate(nodes):
        if index not in free_nodes:
            index_map[key] = index + 1

    return index_map


def deserialize_red_black_tree_nodes(
    data: bytes,
    key_size: int,
    value_size: int,
    deserialize_key,
    deserialize_value,
) -> Tuple[List[Tuple[Any, Any]], Set[int]]:
    offset = 0

    nodes = []

    # Skip RBTree header
    offset += 16

    # Skip node allocator size
    offset += 8
    bump_index = struct.unpack_from("<i", data, offset)[0]
    offset += 4
    free_list_head = struct.unpack_from("<i", data, offset)[0]
    offset += 4

    free_list_pointers = []

    index = 0
    while offset < len(data) and index < bump_index - 1:
        registers = []
        for i in range(4):
            registers.append(struct.unpack_from("<i", data, offset)[0])
            offset += 4

        key = deserialize_key(data, offset)
        offset += key_size
        value = deserialize_value(data, offset)
        offset += value_size
        nodes.append((key, value))
        free_list_pointers.append((index, registers[0]))
        index += 1

    free_nodes = set()
    index_to_remove = free_list_head - 1

    counter = 0
    while free_list_head < bump_index:
        next_node = free_list_pointers[free_list_head - 1]
        index_to_remove, free_list_head = next_node
        free_nodes.add(index_to_remove)
        counter += 1
        if counter > bump_index:
            raise ValueError("Infinite loop detected")

    return nodes, free_nodes
