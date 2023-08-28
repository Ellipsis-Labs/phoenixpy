from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class MarketSizeParamsJSON(typing.TypedDict):
    bids_size: int
    asks_size: int
    num_seats: int


@dataclass
class MarketSizeParams:
    layout: typing.ClassVar = borsh.CStruct(
        "bids_size" / borsh.U64, "asks_size" / borsh.U64, "num_seats" / borsh.U64
    )
    bids_size: int
    asks_size: int
    num_seats: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "MarketSizeParams":
        return cls(
            bids_size=obj.bids_size, asks_size=obj.asks_size, num_seats=obj.num_seats
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "bids_size": self.bids_size,
            "asks_size": self.asks_size,
            "num_seats": self.num_seats,
        }

    def to_json(self) -> MarketSizeParamsJSON:
        return {
            "bids_size": self.bids_size,
            "asks_size": self.asks_size,
            "num_seats": self.num_seats,
        }

    @classmethod
    def from_json(cls, obj: MarketSizeParamsJSON) -> "MarketSizeParams":
        return cls(
            bids_size=obj["bids_size"],
            asks_size=obj["asks_size"],
            num_seats=obj["num_seats"],
        )
