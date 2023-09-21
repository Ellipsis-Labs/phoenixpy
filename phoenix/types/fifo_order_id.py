from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class FIFOOrderIdJSON(typing.TypedDict):
    price_in_ticks: int
    order_sequence_number: int


@dataclass
class FIFOOrderId:
    layout: typing.ClassVar = borsh.CStruct(
        "price_in_ticks" / borsh.U64, "order_sequence_number" / borsh.U64
    )
    price_in_ticks: int
    order_sequence_number: int

    @staticmethod
    def size():
        return 16

    @classmethod
    def from_decoded(cls, obj: Container) -> "FIFOOrderId":
        return cls(
            price_in_ticks=obj.price_in_ticks,
            order_sequence_number=obj.order_sequence_number,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "price_in_ticks": self.price_in_ticks,
            "order_sequence_number": self.order_sequence_number,
        }

    def to_json(self) -> FIFOOrderIdJSON:
        return {
            "price_in_ticks": self.price_in_ticks,
            "order_sequence_number": self.order_sequence_number,
        }

    @classmethod
    def from_json(cls, obj: FIFOOrderIdJSON) -> "FIFOOrderId":
        return cls(
            price_in_ticks=obj["price_in_ticks"],
            order_sequence_number=obj["order_sequence_number"],
        )

    def __hash__(self):
        return hash((self.price_in_ticks, self.order_sequence_number))

    def __repr__(self) -> str:
        return f"FIFOOrderId(price_in_ticks={self.price_in_ticks}, order_sequence_number={self.order_sequence_number})"

    def __lt__(self, other: FIFOOrderId) -> bool:
        if self.order_sequence_number & 1 << 63 != 0:
            if self.price_in_ticks == other.price_in_ticks:
                return self.order_sequence_number < other.order_sequence_number
            else:
                return self.price_in_ticks < other.price_in_ticks
        else:
            if self.price_in_ticks == other.price_in_ticks:
                return self.order_sequence_number > other.order_sequence_number
            else:
                return self.price_in_ticks > other.price_in_ticks

    def to_int(self) -> int:
        return self.price_in_ticks << 64 | self.order_sequence_number

    @classmethod
    def from_int(cls, order_id) -> "FIFOOrderId":
        return FIFOOrderId(
            price_in_ticks=order_id >> 64,
            order_sequence_number=order_id & 0xFFFFFFFFFFFFFFFF,
        )
