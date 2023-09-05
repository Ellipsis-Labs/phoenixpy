from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
from solders.pubkey import Pubkey
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh


class SeatJSON(typing.TypedDict):
    discriminant: int
    market: str
    trader: str
    approval_status: int
    padding: list[int]


@dataclass
class Seat:
    layout: typing.ClassVar = borsh.CStruct(
        "discriminant" / borsh.U64,
        "market" / BorshPubkey,
        "trader" / BorshPubkey,
        "approval_status" / borsh.U64,
        "padding" / borsh.U64[6],
    )
    discriminant: int
    market: Pubkey
    trader: Pubkey
    approval_status: int
    padding: list[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "Seat":
        return cls(
            discriminant=obj.discriminant,
            market=obj.market,
            trader=obj.trader,
            approval_status=obj.approval_status,
            padding=obj.padding,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "discriminant": self.discriminant,
            "market": self.market,
            "trader": self.trader,
            "approval_status": self.approval_status,
            "padding": self.padding,
        }

    def to_json(self) -> SeatJSON:
        return {
            "discriminant": self.discriminant,
            "market": str(self.market),
            "trader": str(self.trader),
            "approval_status": self.approval_status,
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: SeatJSON) -> "Seat":
        return cls(
            discriminant=obj["discriminant"],
            market=Pubkey.from_string(obj["market"]),
            trader=Pubkey.from_string(obj["trader"]),
            approval_status=obj["approval_status"],
            padding=obj["padding"],
        )
