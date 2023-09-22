from dataclasses import dataclass
from decimal import Decimal
from traceback import StackSummary
from typing import Optional, Union

from phoenix.types.fifo_order_id import FIFOOrderId
from phoenix.types.side import Ask, Bid
from solders.pubkey import Pubkey


@dataclass
class FilledOrder:
    order_id: int
    market_pubkey: Pubkey
    sequence_number: int
    slot: int
    unix_timestamp_in_seconds: int
    taker_side: Union[Bid, Ask]
    price: Decimal
    quantity_filled: Decimal
    quantity_remaining: Decimal
    taker_pubkey: Pubkey
    maker_pubkey: Pubkey


@dataclass
class OpenOrder:
    order_id: int
    client_order_id: int
    market_pubkey: Pubkey
    sequence_number: int
    slot: int
    side: Union[Bid, Ask]
    price: Decimal
    quantity_placed: Decimal
    unix_timestamp_in_seconds: int
    side: Union[Bid, Ask]
    maker_pubkey: Pubkey


@dataclass
class CancelledOrder:
    order_id: int
    market_pubkey: Pubkey
    sequence_number: int
    slot: int
    unix_timestamp_in_seconds: int
    side: Union[Bid, Ask]
    price: Decimal
    quantity_removed: Decimal
    quantity_remaining: Decimal
    maker_pubkey: Pubkey


@dataclass
class OrderSubscribeError:
    message: str
    reconnection_count: int
    reconnected: bool
    error_count: int
    traceback: Optional[StackSummary]
    exception: Exception


OrderSubscribeResponse = Union[
    FilledOrder,
    OpenOrder,
    CancelledOrder,
    OrderSubscribeError,
]
