from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class ReduceEventJSON(typing.TypedDict):
    index: int
    order_sequence_number: int
    price_in_ticks: int
    base_lots_removed: int
    base_lots_remaining: int


@dataclass
class ReduceEvent:
    layout: typing.ClassVar = borsh.CStruct(
        "index" / borsh.U16,
        "order_sequence_number" / borsh.U64,
        "price_in_ticks" / borsh.U64,
        "base_lots_removed" / borsh.U64,
        "base_lots_remaining" / borsh.U64,
    )
    index: int
    order_sequence_number: int
    price_in_ticks: int
    base_lots_removed: int
    base_lots_remaining: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "ReduceEvent":
        return cls(
            index=obj.index,
            order_sequence_number=obj.order_sequence_number,
            price_in_ticks=obj.price_in_ticks,
            base_lots_removed=obj.base_lots_removed,
            base_lots_remaining=obj.base_lots_remaining,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "index": self.index,
            "order_sequence_number": self.order_sequence_number,
            "price_in_ticks": self.price_in_ticks,
            "base_lots_removed": self.base_lots_removed,
            "base_lots_remaining": self.base_lots_remaining,
        }

    def to_json(self) -> ReduceEventJSON:
        return {
            "index": self.index,
            "order_sequence_number": self.order_sequence_number,
            "price_in_ticks": self.price_in_ticks,
            "base_lots_removed": self.base_lots_removed,
            "base_lots_remaining": self.base_lots_remaining,
        }

    @classmethod
    def from_json(cls, obj: ReduceEventJSON) -> "ReduceEvent":
        return cls(
            index=obj["index"],
            order_sequence_number=obj["order_sequence_number"],
            price_in_ticks=obj["price_in_ticks"],
            base_lots_removed=obj["base_lots_removed"],
            base_lots_remaining=obj["base_lots_remaining"],
        )
