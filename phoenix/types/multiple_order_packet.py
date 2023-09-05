from __future__ import annotations
from . import (
    condensed_order,
    failed_multiple_limit_order_behavior,
)
import typing
from dataclasses import dataclass
from construct import Container, Construct
import borsh_construct as borsh


class MultipleOrderPacketJSON(typing.TypedDict):
    bids: list[condensed_order.CondensedOrderJSON]
    asks: list[condensed_order.CondensedOrderJSON]
    client_order_id: typing.Optional[int]
    failed_multiple_limit_order_behavior: failed_multiple_limit_order_behavior.FailedMultipleLimitOrderBehaviorJSON


@dataclass
class MultipleOrderPacket:
    layout: typing.ClassVar = borsh.CStruct(
        "bids"
        / borsh.Vec(typing.cast(Construct, condensed_order.CondensedOrder.layout)),
        "asks"
        / borsh.Vec(typing.cast(Construct, condensed_order.CondensedOrder.layout)),
        "client_order_id" / borsh.Option(borsh.U128),
        "failed_multiple_limit_order_behavior"
        / failed_multiple_limit_order_behavior.layout,
    )
    bids: list[condensed_order.CondensedOrder]
    asks: list[condensed_order.CondensedOrder]
    client_order_id: typing.Optional[int]
    failed_multiple_limit_order_behavior: failed_multiple_limit_order_behavior.FailedMultipleLimitOrderBehaviorKind

    @classmethod
    def from_decoded(cls, obj: Container) -> "MultipleOrderPacket":
        return cls(
            bids=list(
                map(
                    lambda item: condensed_order.CondensedOrder.from_decoded(item),
                    obj.bids,
                )
            ),
            asks=list(
                map(
                    lambda item: condensed_order.CondensedOrder.from_decoded(item),
                    obj.asks,
                )
            ),
            client_order_id=obj.client_order_id,
            failed_multiple_limit_order_behavior=failed_multiple_limit_order_behavior.from_decoded(
                obj.failed_multiple_limit_order_behavior
            ),
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "bids": list(map(lambda item: item.to_encodable(), self.bids)),
            "asks": list(map(lambda item: item.to_encodable(), self.asks)),
            "client_order_id": self.client_order_id,
            "failed_multiple_limit_order_behavior": self.failed_multiple_limit_order_behavior.to_encodable(),
        }

    def to_json(self) -> MultipleOrderPacketJSON:
        return {
            "bids": list(map(lambda item: item.to_json(), self.bids)),
            "asks": list(map(lambda item: item.to_json(), self.asks)),
            "client_order_id": self.client_order_id,
            "failed_multiple_limit_order_behavior": self.failed_multiple_limit_order_behavior.to_json(),
        }

    @classmethod
    def from_json(cls, obj: MultipleOrderPacketJSON) -> "MultipleOrderPacket":
        return cls(
            bids=list(
                map(
                    lambda item: condensed_order.CondensedOrder.from_json(item),
                    obj["bids"],
                )
            ),
            asks=list(
                map(
                    lambda item: condensed_order.CondensedOrder.from_json(item),
                    obj["asks"],
                )
            ),
            client_order_id=obj["client_order_id"],
            failed_multiple_limit_order_behavior=failed_multiple_limit_order_behavior.from_json(
                obj["failed_multiple_limit_order_behavior"]
            ),
        )
