from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class PlaceEventJSON(typing.TypedDict):
    index: int
    order_sequence_number: int
    client_order_id: int
    price_in_ticks: int
    base_lots_placed: int


@dataclass
class PlaceEvent:
    layout: typing.ClassVar = borsh.CStruct(
        "index" / borsh.U16,
        "order_sequence_number" / borsh.U64,
        "client_order_id" / borsh.U128,
        "price_in_ticks" / borsh.U64,
        "base_lots_placed" / borsh.U64,
    )
    index: int
    order_sequence_number: int
    client_order_id: int
    price_in_ticks: int
    base_lots_placed: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "PlaceEvent":
        return cls(
            index=obj.index,
            order_sequence_number=obj.order_sequence_number,
            client_order_id=obj.client_order_id,
            price_in_ticks=obj.price_in_ticks,
            base_lots_placed=obj.base_lots_placed,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "index": self.index,
            "order_sequence_number": self.order_sequence_number,
            "client_order_id": self.client_order_id,
            "price_in_ticks": self.price_in_ticks,
            "base_lots_placed": self.base_lots_placed,
        }

    def to_json(self) -> PlaceEventJSON:
        return {
            "index": self.index,
            "order_sequence_number": self.order_sequence_number,
            "client_order_id": self.client_order_id,
            "price_in_ticks": self.price_in_ticks,
            "base_lots_placed": self.base_lots_placed,
        }

    @classmethod
    def from_json(cls, obj: PlaceEventJSON) -> "PlaceEvent":
        return cls(
            index=obj["index"],
            order_sequence_number=obj["order_sequence_number"],
            client_order_id=obj["client_order_id"],
            price_in_ticks=obj["price_in_ticks"],
            base_lots_placed=obj["base_lots_placed"],
        )
