from __future__ import annotations
from . import (
    side,
)
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class CancelUpToParamsJSON(typing.TypedDict):
    side: side.SideJSON
    tick_limit: typing.Optional[int]
    num_orders_to_search: typing.Optional[int]
    num_orders_to_cancel: typing.Optional[int]


@dataclass
class CancelUpToParams:
    layout: typing.ClassVar = borsh.CStruct(
        "side" / side.layout,
        "tick_limit" / borsh.Option(borsh.U64),
        "num_orders_to_search" / borsh.Option(borsh.U32),
        "num_orders_to_cancel" / borsh.Option(borsh.U32),
    )
    side: side.SideKind
    tick_limit: typing.Optional[int]
    num_orders_to_search: typing.Optional[int]
    num_orders_to_cancel: typing.Optional[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "CancelUpToParams":
        return cls(
            side=side.from_decoded(obj.side),
            tick_limit=obj.tick_limit,
            num_orders_to_search=obj.num_orders_to_search,
            num_orders_to_cancel=obj.num_orders_to_cancel,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "side": self.side.to_encodable(),
            "tick_limit": self.tick_limit,
            "num_orders_to_search": self.num_orders_to_search,
            "num_orders_to_cancel": self.num_orders_to_cancel,
        }

    def to_json(self) -> CancelUpToParamsJSON:
        return {
            "side": self.side.to_json(),
            "tick_limit": self.tick_limit,
            "num_orders_to_search": self.num_orders_to_search,
            "num_orders_to_cancel": self.num_orders_to_cancel,
        }

    @classmethod
    def from_json(cls, obj: CancelUpToParamsJSON) -> "CancelUpToParams":
        return cls(
            side=side.from_json(obj["side"]),
            tick_limit=obj["tick_limit"],
            num_orders_to_search=obj["num_orders_to_search"],
            num_orders_to_cancel=obj["num_orders_to_cancel"],
        )
