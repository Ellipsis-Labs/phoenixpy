from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class CondensedOrderJSON(typing.TypedDict):
    price_in_ticks: int
    size_in_base_lots: int
    last_valid_slot: typing.Optional[int]
    last_valid_unix_timestamp_in_seconds: typing.Optional[int]


@dataclass
class CondensedOrder:
    layout: typing.ClassVar = borsh.CStruct(
        "price_in_ticks" / borsh.U64,
        "size_in_base_lots" / borsh.U64,
        "last_valid_slot" / borsh.Option(borsh.U64),
        "last_valid_unix_timestamp_in_seconds" / borsh.Option(borsh.U64),
    )
    price_in_ticks: int
    size_in_base_lots: int
    last_valid_slot: typing.Optional[int]
    last_valid_unix_timestamp_in_seconds: typing.Optional[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "CondensedOrder":
        return cls(
            price_in_ticks=obj.price_in_ticks,
            size_in_base_lots=obj.size_in_base_lots,
            last_valid_slot=obj.last_valid_slot,
            last_valid_unix_timestamp_in_seconds=obj.last_valid_unix_timestamp_in_seconds,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "price_in_ticks": self.price_in_ticks,
            "size_in_base_lots": self.size_in_base_lots,
            "last_valid_slot": self.last_valid_slot,
            "last_valid_unix_timestamp_in_seconds": self.last_valid_unix_timestamp_in_seconds,
        }

    def to_json(self) -> CondensedOrderJSON:
        return {
            "price_in_ticks": self.price_in_ticks,
            "size_in_base_lots": self.size_in_base_lots,
            "last_valid_slot": self.last_valid_slot,
            "last_valid_unix_timestamp_in_seconds": self.last_valid_unix_timestamp_in_seconds,
        }

    @classmethod
    def from_json(cls, obj: CondensedOrderJSON) -> "CondensedOrder":
        return cls(
            price_in_ticks=obj["price_in_ticks"],
            size_in_base_lots=obj["size_in_base_lots"],
            last_valid_slot=obj["last_valid_slot"],
            last_valid_unix_timestamp_in_seconds=obj[
                "last_valid_unix_timestamp_in_seconds"
            ],
        )
