from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class TraderStateJSON(typing.TypedDict):
    quote_lots_locked: int
    quote_lots_free: int
    base_lots_locked: int
    base_lots_free: int
    padding: list[int]


@dataclass
class TraderState:
    layout: typing.ClassVar = borsh.CStruct(
        "quote_lots_locked" / borsh.U64,
        "quote_lots_free" / borsh.U64,
        "base_lots_locked" / borsh.U64,
        "base_lots_free" / borsh.U64,
        "padding" / borsh.U64[8],
    )
    quote_lots_locked: int
    quote_lots_free: int
    base_lots_locked: int
    base_lots_free: int
    padding: list[int]

    @staticmethod
    def size():
        return 96

    @classmethod
    def from_decoded(cls, obj: Container) -> "TraderState":
        return cls(
            quote_lots_locked=obj.quote_lots_locked,
            quote_lots_free=obj.quote_lots_free,
            base_lots_locked=obj.base_lots_locked,
            base_lots_free=obj.base_lots_free,
            padding=obj.padding,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "quote_lots_locked": self.quote_lots_locked,
            "quote_lots_free": self.quote_lots_free,
            "base_lots_locked": self.base_lots_locked,
            "base_lots_free": self.base_lots_free,
            "padding": self.padding,
        }

    def to_json(self) -> TraderStateJSON:
        return {
            "quote_lots_locked": self.quote_lots_locked,
            "quote_lots_free": self.quote_lots_free,
            "base_lots_locked": self.base_lots_locked,
            "base_lots_free": self.base_lots_free,
            "padding": self.padding,
        }

    @classmethod
    def from_json(cls, obj: TraderStateJSON) -> "TraderState":
        return cls(
            quote_lots_locked=obj["quote_lots_locked"],
            quote_lots_free=obj["quote_lots_free"],
            base_lots_locked=obj["base_lots_locked"],
            base_lots_free=obj["base_lots_free"],
            padding=obj["padding"],
        )

    def __eq__(self, other: TraderState) -> bool:
        return (
            self.quote_lots_locked == other.quote_lots_locked
            and self.quote_lots_free == other.quote_lots_free
            and self.base_lots_locked == other.base_lots_locked
            and self.base_lots_free == other.base_lots_free
        )
