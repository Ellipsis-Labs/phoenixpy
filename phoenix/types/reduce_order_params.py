from __future__ import annotations
from . import (
    cancel_order_params,
)
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class ReduceOrderParamsJSON(typing.TypedDict):
    base_params: cancel_order_params.CancelOrderParamsJSON
    size: int


@dataclass
class ReduceOrderParams:
    layout: typing.ClassVar = borsh.CStruct(
        "base_params" / cancel_order_params.CancelOrderParams.layout, "size" / borsh.U64
    )
    base_params: cancel_order_params.CancelOrderParams
    size: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "ReduceOrderParams":
        return cls(
            base_params=cancel_order_params.CancelOrderParams.from_decoded(
                obj.base_params
            ),
            size=obj.size,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {"base_params": self.base_params.to_encodable(), "size": self.size}

    def to_json(self) -> ReduceOrderParamsJSON:
        return {"base_params": self.base_params.to_json(), "size": self.size}

    @classmethod
    def from_json(cls, obj: ReduceOrderParamsJSON) -> "ReduceOrderParams":
        return cls(
            base_params=cancel_order_params.CancelOrderParams.from_json(
                obj["base_params"]
            ),
            size=obj["size"],
        )
