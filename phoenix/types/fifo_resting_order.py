from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class FIFORestingOrderJSON(typing.TypedDict):
    trader_index: int
    num_base_lots: int
    last_valid_slot: int
    last_valid_unix_timestamp_in_seconds: int


@dataclass
class FIFORestingOrder:
    layout: typing.ClassVar = borsh.CStruct(
        "trader_index" / borsh.U64,
        "num_base_lots" / borsh.U64,
        "last_valid_slot" / borsh.U64,
        "last_valid_unix_timestamp_in_seconds" / borsh.U64,
    )
    trader_index: int
    num_base_lots: int
    last_valid_slot: int
    last_valid_unix_timestamp_in_seconds: int

    @staticmethod
    def size():
        return 32

    @classmethod
    def from_decoded(cls, obj: Container) -> "FIFORestingOrder":
        return cls(
            trader_index=obj.trader_index,
            num_base_lots=obj.num_base_lots,
            last_valid_slot=obj.last_valid_slot,
            last_valid_unix_timestamp_in_seconds=obj.last_valid_unix_timestamp_in_seconds,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "trader_index": self.trader_index,
            "num_base_lots": self.num_base_lots,
            "last_valid_slot": self.last_valid_slot,
            "last_valid_unix_timestamp_in_seconds": self.last_valid_unix_timestamp_in_seconds,
        }

    def to_json(self) -> FIFORestingOrderJSON:
        return {
            "trader_index": self.trader_index,
            "num_base_lots": self.num_base_lots,
            "last_valid_slot": self.last_valid_slot,
            "last_valid_unix_timestamp_in_seconds": self.last_valid_unix_timestamp_in_seconds,
        }

    @classmethod
    def from_json(cls, obj: FIFORestingOrderJSON) -> "FIFORestingOrder":
        return cls(
            trader_index=obj["trader_index"],
            num_base_lots=obj["num_base_lots"],
            last_valid_slot=obj["last_valid_slot"],
            last_valid_unix_timestamp_in_seconds=obj[
                "last_valid_unix_timestamp_in_seconds"
            ],
        )
