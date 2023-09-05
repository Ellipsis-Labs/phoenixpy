from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
from solders.pubkey import Pubkey
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh


class FillEventJSON(typing.TypedDict):
    index: int
    maker_id: str
    order_sequence_number: int
    price_in_ticks: int
    base_lots_filled: int
    base_lots_remaining: int


@dataclass
class FillEvent:
    layout: typing.ClassVar = borsh.CStruct(
        "index" / borsh.U16,
        "maker_id" / BorshPubkey,
        "order_sequence_number" / borsh.U64,
        "price_in_ticks" / borsh.U64,
        "base_lots_filled" / borsh.U64,
        "base_lots_remaining" / borsh.U64,
    )
    index: int
    maker_id: Pubkey
    order_sequence_number: int
    price_in_ticks: int
    base_lots_filled: int
    base_lots_remaining: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "FillEvent":
        return cls(
            index=obj.index,
            maker_id=obj.maker_id,
            order_sequence_number=obj.order_sequence_number,
            price_in_ticks=obj.price_in_ticks,
            base_lots_filled=obj.base_lots_filled,
            base_lots_remaining=obj.base_lots_remaining,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "index": self.index,
            "maker_id": self.maker_id,
            "order_sequence_number": self.order_sequence_number,
            "price_in_ticks": self.price_in_ticks,
            "base_lots_filled": self.base_lots_filled,
            "base_lots_remaining": self.base_lots_remaining,
        }

    def to_json(self) -> FillEventJSON:
        return {
            "index": self.index,
            "maker_id": str(self.maker_id),
            "order_sequence_number": self.order_sequence_number,
            "price_in_ticks": self.price_in_ticks,
            "base_lots_filled": self.base_lots_filled,
            "base_lots_remaining": self.base_lots_remaining,
        }

    @classmethod
    def from_json(cls, obj: FillEventJSON) -> "FillEvent":
        return cls(
            index=obj["index"],
            maker_id=Pubkey.from_string(obj["maker_id"]),
            order_sequence_number=obj["order_sequence_number"],
            price_in_ticks=obj["price_in_ticks"],
            base_lots_filled=obj["base_lots_filled"],
            base_lots_remaining=obj["base_lots_remaining"],
        )
