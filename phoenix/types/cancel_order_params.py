from __future__ import annotations
from . import (
    side,
)
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class CancelOrderParamsJSON(typing.TypedDict):
    side: side.SideJSON
    price_in_ticks: int
    order_sequence_number: int


@dataclass
class CancelOrderParams:
    layout: typing.ClassVar = borsh.CStruct(
        "side" / side.layout,
        "price_in_ticks" / borsh.U64,
        "order_sequence_number" / borsh.U64,
    )
    side: side.SideKind
    price_in_ticks: int
    order_sequence_number: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "CancelOrderParams":
        return cls(
            side=side.from_decoded(obj.side),
            price_in_ticks=obj.price_in_ticks,
            order_sequence_number=obj.order_sequence_number,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "side": self.side.to_encodable(),
            "price_in_ticks": self.price_in_ticks,
            "order_sequence_number": self.order_sequence_number,
        }

    def to_json(self) -> CancelOrderParamsJSON:
        return {
            "side": self.side.to_json(),
            "price_in_ticks": self.price_in_ticks,
            "order_sequence_number": self.order_sequence_number,
        }

    @classmethod
    def from_json(cls, obj: CancelOrderParamsJSON) -> "CancelOrderParams":
        return cls(
            side=side.from_json(obj["side"]),
            price_in_ticks=obj["price_in_ticks"],
            order_sequence_number=obj["order_sequence_number"],
        )
