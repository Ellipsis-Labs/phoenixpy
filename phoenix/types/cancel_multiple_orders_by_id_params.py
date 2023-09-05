from __future__ import annotations
from . import (
    cancel_order_params,
)
import typing
from dataclasses import dataclass
from construct import Container, Construct
import borsh_construct as borsh


class CancelMultipleOrdersByIdParamsJSON(typing.TypedDict):
    orders: list[cancel_order_params.CancelOrderParamsJSON]


@dataclass
class CancelMultipleOrdersByIdParams:
    layout: typing.ClassVar = borsh.CStruct(
        "orders"
        / borsh.Vec(
            typing.cast(Construct, cancel_order_params.CancelOrderParams.layout)
        )
    )
    orders: list[cancel_order_params.CancelOrderParams]

    @classmethod
    def from_decoded(cls, obj: Container) -> "CancelMultipleOrdersByIdParams":
        return cls(
            orders=list(
                map(
                    lambda item: cancel_order_params.CancelOrderParams.from_decoded(
                        item
                    ),
                    obj.orders,
                )
            )
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {"orders": list(map(lambda item: item.to_encodable(), self.orders))}

    def to_json(self) -> CancelMultipleOrdersByIdParamsJSON:
        return {"orders": list(map(lambda item: item.to_json(), self.orders))}

    @classmethod
    def from_json(
        cls, obj: CancelMultipleOrdersByIdParamsJSON
    ) -> "CancelMultipleOrdersByIdParams":
        return cls(
            orders=list(
                map(
                    lambda item: cancel_order_params.CancelOrderParams.from_json(item),
                    obj["orders"],
                )
            )
        )
