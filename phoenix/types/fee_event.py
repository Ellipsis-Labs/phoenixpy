from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class FeeEventJSON(typing.TypedDict):
    index: int
    fees_collected_in_quote_lots: int


@dataclass
class FeeEvent:
    layout: typing.ClassVar = borsh.CStruct(
        "index" / borsh.U16, "fees_collected_in_quote_lots" / borsh.U64
    )
    index: int
    fees_collected_in_quote_lots: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "FeeEvent":
        return cls(
            index=obj.index,
            fees_collected_in_quote_lots=obj.fees_collected_in_quote_lots,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "index": self.index,
            "fees_collected_in_quote_lots": self.fees_collected_in_quote_lots,
        }

    def to_json(self) -> FeeEventJSON:
        return {
            "index": self.index,
            "fees_collected_in_quote_lots": self.fees_collected_in_quote_lots,
        }

    @classmethod
    def from_json(cls, obj: FeeEventJSON) -> "FeeEvent":
        return cls(
            index=obj["index"],
            fees_collected_in_quote_lots=obj["fees_collected_in_quote_lots"],
        )
