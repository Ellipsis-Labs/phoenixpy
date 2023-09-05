from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class DepositParamsJSON(typing.TypedDict):
    quote_lots_to_deposit: int
    base_lots_to_deposit: int


@dataclass
class DepositParams:
    layout: typing.ClassVar = borsh.CStruct(
        "quote_lots_to_deposit" / borsh.U64, "base_lots_to_deposit" / borsh.U64
    )
    quote_lots_to_deposit: int
    base_lots_to_deposit: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "DepositParams":
        return cls(
            quote_lots_to_deposit=obj.quote_lots_to_deposit,
            base_lots_to_deposit=obj.base_lots_to_deposit,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "quote_lots_to_deposit": self.quote_lots_to_deposit,
            "base_lots_to_deposit": self.base_lots_to_deposit,
        }

    def to_json(self) -> DepositParamsJSON:
        return {
            "quote_lots_to_deposit": self.quote_lots_to_deposit,
            "base_lots_to_deposit": self.base_lots_to_deposit,
        }

    @classmethod
    def from_json(cls, obj: DepositParamsJSON) -> "DepositParams":
        return cls(
            quote_lots_to_deposit=obj["quote_lots_to_deposit"],
            base_lots_to_deposit=obj["base_lots_to_deposit"],
        )
