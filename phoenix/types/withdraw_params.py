from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class WithdrawParamsJSON(typing.TypedDict):
    quote_lots_to_withdraw: typing.Optional[int]
    base_lots_to_withdraw: typing.Optional[int]


@dataclass
class WithdrawParams:
    layout: typing.ClassVar = borsh.CStruct(
        "quote_lots_to_withdraw" / borsh.Option(borsh.U64),
        "base_lots_to_withdraw" / borsh.Option(borsh.U64),
    )
    quote_lots_to_withdraw: typing.Optional[int]
    base_lots_to_withdraw: typing.Optional[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "WithdrawParams":
        return cls(
            quote_lots_to_withdraw=obj.quote_lots_to_withdraw,
            base_lots_to_withdraw=obj.base_lots_to_withdraw,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "quote_lots_to_withdraw": self.quote_lots_to_withdraw,
            "base_lots_to_withdraw": self.base_lots_to_withdraw,
        }

    def to_json(self) -> WithdrawParamsJSON:
        return {
            "quote_lots_to_withdraw": self.quote_lots_to_withdraw,
            "base_lots_to_withdraw": self.base_lots_to_withdraw,
        }

    @classmethod
    def from_json(cls, obj: WithdrawParamsJSON) -> "WithdrawParams":
        return cls(
            quote_lots_to_withdraw=obj["quote_lots_to_withdraw"],
            base_lots_to_withdraw=obj["base_lots_to_withdraw"],
        )
