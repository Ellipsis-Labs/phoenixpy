from __future__ import annotations
from . import (
    side,
    self_trade_behavior,
)
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class PostOnlyJSONValue(typing.TypedDict):
    side: side.SideJSON
    price_in_ticks: int
    num_base_lots: int
    client_order_id: int
    reject_post_only: bool
    use_only_deposited_funds: bool
    last_valid_slot: typing.Optional[int]
    last_valid_unix_timestamp_in_seconds: typing.Optional[int]
    fail_silently_on_insufficient_funds: bool


class LimitJSONValue(typing.TypedDict):
    side: side.SideJSON
    price_in_ticks: int
    num_base_lots: int
    self_trade_behavior: self_trade_behavior.SelfTradeBehaviorJSON
    match_limit: typing.Optional[int]
    client_order_id: int
    use_only_deposited_funds: bool
    last_valid_slot: typing.Optional[int]
    last_valid_unix_timestamp_in_seconds: typing.Optional[int]
    fail_silently_on_insufficient_funds: bool


class ImmediateOrCancelJSONValue(typing.TypedDict):
    side: side.SideJSON
    price_in_ticks: typing.Optional[int]
    num_base_lots: int
    num_quote_lots: int
    min_base_lots_to_fill: int
    min_quote_lots_to_fill: int
    self_trade_behavior: self_trade_behavior.SelfTradeBehaviorJSON
    match_limit: typing.Optional[int]
    client_order_id: int
    use_only_deposited_funds: bool
    last_valid_slot: typing.Optional[int]
    last_valid_unix_timestamp_in_seconds: typing.Optional[int]


class PostOnlyValue(typing.TypedDict):
    side: side.SideKind
    price_in_ticks: int
    num_base_lots: int
    client_order_id: int
    reject_post_only: bool
    use_only_deposited_funds: bool
    last_valid_slot: typing.Optional[int]
    last_valid_unix_timestamp_in_seconds: typing.Optional[int]
    fail_silently_on_insufficient_funds: bool


class LimitValue(typing.TypedDict):
    side: side.SideKind
    price_in_ticks: int
    num_base_lots: int
    self_trade_behavior: self_trade_behavior.SelfTradeBehaviorKind
    match_limit: typing.Optional[int]
    client_order_id: int
    use_only_deposited_funds: bool
    last_valid_slot: typing.Optional[int]
    last_valid_unix_timestamp_in_seconds: typing.Optional[int]
    fail_silently_on_insufficient_funds: bool


class ImmediateOrCancelValue(typing.TypedDict):
    side: side.SideKind
    price_in_ticks: typing.Optional[int]
    num_base_lots: int
    num_quote_lots: int
    min_base_lots_to_fill: int
    min_quote_lots_to_fill: int
    self_trade_behavior: self_trade_behavior.SelfTradeBehaviorKind
    match_limit: typing.Optional[int]
    client_order_id: int
    use_only_deposited_funds: bool
    last_valid_slot: typing.Optional[int]
    last_valid_unix_timestamp_in_seconds: typing.Optional[int]


class PostOnlyJSON(typing.TypedDict):
    value: PostOnlyJSONValue
    kind: typing.Literal["PostOnly"]


class LimitJSON(typing.TypedDict):
    value: LimitJSONValue
    kind: typing.Literal["Limit"]


class ImmediateOrCancelJSON(typing.TypedDict):
    value: ImmediateOrCancelJSONValue
    kind: typing.Literal["ImmediateOrCancel"]


@dataclass
class PostOnly:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "PostOnly"
    value: PostOnlyValue

    def to_json(self) -> PostOnlyJSON:
        return PostOnlyJSON(
            kind="PostOnly",
            value={
                "side": self.value["side"].to_json(),
                "price_in_ticks": self.value["price_in_ticks"],
                "num_base_lots": self.value["num_base_lots"],
                "client_order_id": self.value["client_order_id"],
                "reject_post_only": self.value["reject_post_only"],
                "use_only_deposited_funds": self.value["use_only_deposited_funds"],
                "last_valid_slot": self.value["last_valid_slot"],
                "last_valid_unix_timestamp_in_seconds": self.value[
                    "last_valid_unix_timestamp_in_seconds"
                ],
                "fail_silently_on_insufficient_funds": self.value[
                    "fail_silently_on_insufficient_funds"
                ],
            },
        )

    def to_encodable(self) -> dict:
        return {
            "PostOnly": {
                "side": self.value["side"].to_encodable(),
                "price_in_ticks": self.value["price_in_ticks"],
                "num_base_lots": self.value["num_base_lots"],
                "client_order_id": self.value["client_order_id"],
                "reject_post_only": self.value["reject_post_only"],
                "use_only_deposited_funds": self.value["use_only_deposited_funds"],
                "last_valid_slot": self.value["last_valid_slot"],
                "last_valid_unix_timestamp_in_seconds": self.value[
                    "last_valid_unix_timestamp_in_seconds"
                ],
                "fail_silently_on_insufficient_funds": self.value[
                    "fail_silently_on_insufficient_funds"
                ],
            },
        }


@dataclass
class Limit:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Limit"
    value: LimitValue

    def to_json(self) -> LimitJSON:
        return LimitJSON(
            kind="Limit",
            value={
                "side": self.value["side"].to_json(),
                "price_in_ticks": self.value["price_in_ticks"],
                "num_base_lots": self.value["num_base_lots"],
                "self_trade_behavior": self.value["self_trade_behavior"].to_json(),
                "match_limit": self.value["match_limit"],
                "client_order_id": self.value["client_order_id"],
                "use_only_deposited_funds": self.value["use_only_deposited_funds"],
                "last_valid_slot": self.value["last_valid_slot"],
                "last_valid_unix_timestamp_in_seconds": self.value[
                    "last_valid_unix_timestamp_in_seconds"
                ],
                "fail_silently_on_insufficient_funds": self.value[
                    "fail_silently_on_insufficient_funds"
                ],
            },
        )

    def to_encodable(self) -> dict:
        return {
            "Limit": {
                "side": self.value["side"].to_encodable(),
                "price_in_ticks": self.value["price_in_ticks"],
                "num_base_lots": self.value["num_base_lots"],
                "self_trade_behavior": self.value["self_trade_behavior"].to_encodable(),
                "match_limit": self.value["match_limit"],
                "client_order_id": self.value["client_order_id"],
                "use_only_deposited_funds": self.value["use_only_deposited_funds"],
                "last_valid_slot": self.value["last_valid_slot"],
                "last_valid_unix_timestamp_in_seconds": self.value[
                    "last_valid_unix_timestamp_in_seconds"
                ],
                "fail_silently_on_insufficient_funds": self.value[
                    "fail_silently_on_insufficient_funds"
                ],
            },
        }


@dataclass
class ImmediateOrCancel:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "ImmediateOrCancel"
    value: ImmediateOrCancelValue

    def to_json(self) -> ImmediateOrCancelJSON:
        return ImmediateOrCancelJSON(
            kind="ImmediateOrCancel",
            value={
                "side": self.value["side"].to_json(),
                "price_in_ticks": self.value["price_in_ticks"],
                "num_base_lots": self.value["num_base_lots"],
                "num_quote_lots": self.value["num_quote_lots"],
                "min_base_lots_to_fill": self.value["min_base_lots_to_fill"],
                "min_quote_lots_to_fill": self.value["min_quote_lots_to_fill"],
                "self_trade_behavior": self.value["self_trade_behavior"].to_json(),
                "match_limit": self.value["match_limit"],
                "client_order_id": self.value["client_order_id"],
                "use_only_deposited_funds": self.value["use_only_deposited_funds"],
                "last_valid_slot": self.value["last_valid_slot"],
                "last_valid_unix_timestamp_in_seconds": self.value[
                    "last_valid_unix_timestamp_in_seconds"
                ],
            },
        )

    def to_encodable(self) -> dict:
        return {
            "ImmediateOrCancel": {
                "side": self.value["side"].to_encodable(),
                "price_in_ticks": self.value["price_in_ticks"],
                "num_base_lots": self.value["num_base_lots"],
                "num_quote_lots": self.value["num_quote_lots"],
                "min_base_lots_to_fill": self.value["min_base_lots_to_fill"],
                "min_quote_lots_to_fill": self.value["min_quote_lots_to_fill"],
                "self_trade_behavior": self.value["self_trade_behavior"].to_encodable(),
                "match_limit": self.value["match_limit"],
                "client_order_id": self.value["client_order_id"],
                "use_only_deposited_funds": self.value["use_only_deposited_funds"],
                "last_valid_slot": self.value["last_valid_slot"],
                "last_valid_unix_timestamp_in_seconds": self.value[
                    "last_valid_unix_timestamp_in_seconds"
                ],
            },
        }


OrderPacketKind = typing.Union[PostOnly, Limit, ImmediateOrCancel]
OrderPacketJSON = typing.Union[PostOnlyJSON, LimitJSON, ImmediateOrCancelJSON]


def from_decoded(obj: dict) -> OrderPacketKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "PostOnly" in obj:
        val = obj["PostOnly"]
        return PostOnly(
            PostOnlyValue(
                side=side.from_decoded(val["side"]),
                price_in_ticks=val["price_in_ticks"],
                num_base_lots=val["num_base_lots"],
                client_order_id=val["client_order_id"],
                reject_post_only=val["reject_post_only"],
                use_only_deposited_funds=val["use_only_deposited_funds"],
                last_valid_slot=val["last_valid_slot"],
                last_valid_unix_timestamp_in_seconds=val[
                    "last_valid_unix_timestamp_in_seconds"
                ],
                fail_silently_on_insufficient_funds=val[
                    "fail_silently_on_insufficient_funds"
                ],
            )
        )
    if "Limit" in obj:
        val = obj["Limit"]
        return Limit(
            LimitValue(
                side=side.from_decoded(val["side"]),
                price_in_ticks=val["price_in_ticks"],
                num_base_lots=val["num_base_lots"],
                self_trade_behavior=self_trade_behavior.from_decoded(
                    val["self_trade_behavior"]
                ),
                match_limit=val["match_limit"],
                client_order_id=val["client_order_id"],
                use_only_deposited_funds=val["use_only_deposited_funds"],
                last_valid_slot=val["last_valid_slot"],
                last_valid_unix_timestamp_in_seconds=val[
                    "last_valid_unix_timestamp_in_seconds"
                ],
                fail_silently_on_insufficient_funds=val[
                    "fail_silently_on_insufficient_funds"
                ],
            )
        )
    if "ImmediateOrCancel" in obj:
        val = obj["ImmediateOrCancel"]
        return ImmediateOrCancel(
            ImmediateOrCancelValue(
                side=side.from_decoded(val["side"]),
                price_in_ticks=val["price_in_ticks"],
                num_base_lots=val["num_base_lots"],
                num_quote_lots=val["num_quote_lots"],
                min_base_lots_to_fill=val["min_base_lots_to_fill"],
                min_quote_lots_to_fill=val["min_quote_lots_to_fill"],
                self_trade_behavior=self_trade_behavior.from_decoded(
                    val["self_trade_behavior"]
                ),
                match_limit=val["match_limit"],
                client_order_id=val["client_order_id"],
                use_only_deposited_funds=val["use_only_deposited_funds"],
                last_valid_slot=val["last_valid_slot"],
                last_valid_unix_timestamp_in_seconds=val[
                    "last_valid_unix_timestamp_in_seconds"
                ],
            )
        )
    raise ValueError("Invalid enum object")


def from_json(obj: OrderPacketJSON) -> OrderPacketKind:
    if obj["kind"] == "PostOnly":
        post_only_json_value = typing.cast(PostOnlyJSONValue, obj["value"])
        return PostOnly(
            PostOnlyValue(
                side=side.from_json(post_only_json_value["side"]),
                price_in_ticks=post_only_json_value["price_in_ticks"],
                num_base_lots=post_only_json_value["num_base_lots"],
                client_order_id=post_only_json_value["client_order_id"],
                reject_post_only=post_only_json_value["reject_post_only"],
                use_only_deposited_funds=post_only_json_value[
                    "use_only_deposited_funds"
                ],
                last_valid_slot=post_only_json_value["last_valid_slot"],
                last_valid_unix_timestamp_in_seconds=post_only_json_value[
                    "last_valid_unix_timestamp_in_seconds"
                ],
                fail_silently_on_insufficient_funds=post_only_json_value[
                    "fail_silently_on_insufficient_funds"
                ],
            )
        )
    if obj["kind"] == "Limit":
        limit_json_value = typing.cast(LimitJSONValue, obj["value"])
        return Limit(
            LimitValue(
                side=side.from_json(limit_json_value["side"]),
                price_in_ticks=limit_json_value["price_in_ticks"],
                num_base_lots=limit_json_value["num_base_lots"],
                self_trade_behavior=self_trade_behavior.from_json(
                    limit_json_value["self_trade_behavior"]
                ),
                match_limit=limit_json_value["match_limit"],
                client_order_id=limit_json_value["client_order_id"],
                use_only_deposited_funds=limit_json_value["use_only_deposited_funds"],
                last_valid_slot=limit_json_value["last_valid_slot"],
                last_valid_unix_timestamp_in_seconds=limit_json_value[
                    "last_valid_unix_timestamp_in_seconds"
                ],
                fail_silently_on_insufficient_funds=limit_json_value[
                    "fail_silently_on_insufficient_funds"
                ],
            )
        )
    if obj["kind"] == "ImmediateOrCancel":
        immediate_or_cancel_json_value = typing.cast(
            ImmediateOrCancelJSONValue, obj["value"]
        )
        return ImmediateOrCancel(
            ImmediateOrCancelValue(
                side=side.from_json(immediate_or_cancel_json_value["side"]),
                price_in_ticks=immediate_or_cancel_json_value["price_in_ticks"],
                num_base_lots=immediate_or_cancel_json_value["num_base_lots"],
                num_quote_lots=immediate_or_cancel_json_value["num_quote_lots"],
                min_base_lots_to_fill=immediate_or_cancel_json_value[
                    "min_base_lots_to_fill"
                ],
                min_quote_lots_to_fill=immediate_or_cancel_json_value[
                    "min_quote_lots_to_fill"
                ],
                self_trade_behavior=self_trade_behavior.from_json(
                    immediate_or_cancel_json_value["self_trade_behavior"]
                ),
                match_limit=immediate_or_cancel_json_value["match_limit"],
                client_order_id=immediate_or_cancel_json_value["client_order_id"],
                use_only_deposited_funds=immediate_or_cancel_json_value[
                    "use_only_deposited_funds"
                ],
                last_valid_slot=immediate_or_cancel_json_value["last_valid_slot"],
                last_valid_unix_timestamp_in_seconds=immediate_or_cancel_json_value[
                    "last_valid_unix_timestamp_in_seconds"
                ],
            )
        )
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "PostOnly"
    / borsh.CStruct(
        "side" / side.layout,
        "price_in_ticks" / borsh.U64,
        "num_base_lots" / borsh.U64,
        "client_order_id" / borsh.U128,
        "reject_post_only" / borsh.Bool,
        "use_only_deposited_funds" / borsh.Bool,
        "last_valid_slot" / borsh.Option(borsh.U64),
        "last_valid_unix_timestamp_in_seconds" / borsh.Option(borsh.U64),
        "fail_silently_on_insufficient_funds" / borsh.Bool,
    ),
    "Limit"
    / borsh.CStruct(
        "side" / side.layout,
        "price_in_ticks" / borsh.U64,
        "num_base_lots" / borsh.U64,
        "self_trade_behavior" / self_trade_behavior.layout,
        "match_limit" / borsh.Option(borsh.U64),
        "client_order_id" / borsh.U128,
        "use_only_deposited_funds" / borsh.Bool,
        "last_valid_slot" / borsh.Option(borsh.U64),
        "last_valid_unix_timestamp_in_seconds" / borsh.Option(borsh.U64),
        "fail_silently_on_insufficient_funds" / borsh.Bool,
    ),
    "ImmediateOrCancel"
    / borsh.CStruct(
        "side" / side.layout,
        "price_in_ticks" / borsh.Option(borsh.U64),
        "num_base_lots" / borsh.U64,
        "num_quote_lots" / borsh.U64,
        "min_base_lots_to_fill" / borsh.U64,
        "min_quote_lots_to_fill" / borsh.U64,
        "self_trade_behavior" / self_trade_behavior.layout,
        "match_limit" / borsh.Option(borsh.U64),
        "client_order_id" / borsh.U128,
        "use_only_deposited_funds" / borsh.Bool,
        "last_valid_slot" / borsh.Option(borsh.U64),
        "last_valid_unix_timestamp_in_seconds" / borsh.Option(borsh.U64),
    ),
)
