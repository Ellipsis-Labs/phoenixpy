from __future__ import annotations
from . import (
    audit_log_header,
    fill_event,
    reduce_event,
    place_event,
    evict_event,
    fill_summary_event,
    fee_event,
    time_in_force_event,
    expired_order_event,
)
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh

HeaderJSONValue = tuple[audit_log_header.AuditLogHeaderJSON]
FillJSONValue = tuple[fill_event.FillEventJSON]
PlaceJSONValue = tuple[place_event.PlaceEventJSON]
ReduceJSONValue = tuple[reduce_event.ReduceEventJSON]
EvictJSONValue = tuple[evict_event.EvictEventJSON]
FillSummaryJSONValue = tuple[fill_summary_event.FillSummaryEventJSON]
FeeJSONValue = tuple[fee_event.FeeEventJSON]
TimeInForceJSONValue = tuple[time_in_force_event.TimeInForceEventJSON]
ExpiredOrderJSONValue = tuple[expired_order_event.ExpiredOrderEventJSON]
HeaderValue = tuple[audit_log_header.AuditLogHeader]
FillValue = tuple[fill_event.FillEvent]
PlaceValue = tuple[place_event.PlaceEvent]
ReduceValue = tuple[reduce_event.ReduceEvent]
EvictValue = tuple[evict_event.EvictEvent]
FillSummaryValue = tuple[fill_summary_event.FillSummaryEvent]
FeeValue = tuple[fee_event.FeeEvent]
TimeInForceValue = tuple[time_in_force_event.TimeInForceEvent]
ExpiredOrderValue = tuple[expired_order_event.ExpiredOrderEvent]


class UninitializedJSON(typing.TypedDict):
    kind: typing.Literal["Uninitialized"]


class HeaderJSON(typing.TypedDict):
    value: HeaderJSONValue
    kind: typing.Literal["Header"]


class FillJSON(typing.TypedDict):
    value: FillJSONValue
    kind: typing.Literal["Fill"]


class PlaceJSON(typing.TypedDict):
    value: PlaceJSONValue
    kind: typing.Literal["Place"]


class ReduceJSON(typing.TypedDict):
    value: ReduceJSONValue
    kind: typing.Literal["Reduce"]


class EvictJSON(typing.TypedDict):
    value: EvictJSONValue
    kind: typing.Literal["Evict"]


class FillSummaryJSON(typing.TypedDict):
    value: FillSummaryJSONValue
    kind: typing.Literal["FillSummary"]


class FeeJSON(typing.TypedDict):
    value: FeeJSONValue
    kind: typing.Literal["Fee"]


class TimeInForceJSON(typing.TypedDict):
    value: TimeInForceJSONValue
    kind: typing.Literal["TimeInForce"]


class ExpiredOrderJSON(typing.TypedDict):
    value: ExpiredOrderJSONValue
    kind: typing.Literal["ExpiredOrder"]


@dataclass
class Uninitialized:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Uninitialized"

    @classmethod
    def to_json(cls) -> UninitializedJSON:
        return UninitializedJSON(
            kind="Uninitialized",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Uninitialized": {},
        }


@dataclass
class Header:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Header"
    value: HeaderValue

    def to_json(self) -> HeaderJSON:
        return HeaderJSON(
            kind="Header",
            value=(self.value[0].to_json(),),
        )

    def to_encodable(self) -> dict:
        return {
            "Header": {
                "item_0": self.value[0].to_encodable(),
            },
        }


@dataclass
class Fill:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "Fill"
    value: FillValue

    def to_json(self) -> FillJSON:
        return FillJSON(
            kind="Fill",
            value=(self.value[0].to_json(),),
        )

    def to_encodable(self) -> dict:
        return {
            "Fill": {
                "item_0": self.value[0].to_encodable(),
            },
        }


@dataclass
class Place:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "Place"
    value: PlaceValue

    def to_json(self) -> PlaceJSON:
        return PlaceJSON(
            kind="Place",
            value=(self.value[0].to_json(),),
        )

    def to_encodable(self) -> dict:
        return {
            "Place": {
                "item_0": self.value[0].to_encodable(),
            },
        }


@dataclass
class Reduce:
    discriminator: typing.ClassVar = 4
    kind: typing.ClassVar = "Reduce"
    value: ReduceValue

    def to_json(self) -> ReduceJSON:
        return ReduceJSON(
            kind="Reduce",
            value=(self.value[0].to_json(),),
        )

    def to_encodable(self) -> dict:
        return {
            "Reduce": {
                "item_0": self.value[0].to_encodable(),
            },
        }


@dataclass
class Evict:
    discriminator: typing.ClassVar = 5
    kind: typing.ClassVar = "Evict"
    value: EvictValue

    def to_json(self) -> EvictJSON:
        return EvictJSON(
            kind="Evict",
            value=(self.value[0].to_json(),),
        )

    def to_encodable(self) -> dict:
        return {
            "Evict": {
                "item_0": self.value[0].to_encodable(),
            },
        }


@dataclass
class FillSummary:
    discriminator: typing.ClassVar = 6
    kind: typing.ClassVar = "FillSummary"
    value: FillSummaryValue

    def to_json(self) -> FillSummaryJSON:
        return FillSummaryJSON(
            kind="FillSummary",
            value=(self.value[0].to_json(),),
        )

    def to_encodable(self) -> dict:
        return {
            "FillSummary": {
                "item_0": self.value[0].to_encodable(),
            },
        }


@dataclass
class Fee:
    discriminator: typing.ClassVar = 7
    kind: typing.ClassVar = "Fee"
    value: FeeValue

    def to_json(self) -> FeeJSON:
        return FeeJSON(
            kind="Fee",
            value=(self.value[0].to_json(),),
        )

    def to_encodable(self) -> dict:
        return {
            "Fee": {
                "item_0": self.value[0].to_encodable(),
            },
        }


@dataclass
class TimeInForce:
    discriminator: typing.ClassVar = 8
    kind: typing.ClassVar = "TimeInForce"
    value: TimeInForceValue

    def to_json(self) -> TimeInForceJSON:
        return TimeInForceJSON(
            kind="TimeInForce",
            value=(self.value[0].to_json(),),
        )

    def to_encodable(self) -> dict:
        return {
            "TimeInForce": {
                "item_0": self.value[0].to_encodable(),
            },
        }


@dataclass
class ExpiredOrder:
    discriminator: typing.ClassVar = 9
    kind: typing.ClassVar = "ExpiredOrder"
    value: ExpiredOrderValue

    def to_json(self) -> ExpiredOrderJSON:
        return ExpiredOrderJSON(
            kind="ExpiredOrder",
            value=(self.value[0].to_json(),),
        )

    def to_encodable(self) -> dict:
        return {
            "ExpiredOrder": {
                "item_0": self.value[0].to_encodable(),
            },
        }


PhoenixMarketEventKind = typing.Union[
    Uninitialized,
    Header,
    Fill,
    Place,
    Reduce,
    Evict,
    FillSummary,
    Fee,
    TimeInForce,
    ExpiredOrder,
]
PhoenixMarketEventJSON = typing.Union[
    UninitializedJSON,
    HeaderJSON,
    FillJSON,
    PlaceJSON,
    ReduceJSON,
    EvictJSON,
    FillSummaryJSON,
    FeeJSON,
    TimeInForceJSON,
    ExpiredOrderJSON,
]


def from_decoded(obj: dict) -> PhoenixMarketEventKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Uninitialized" in obj:
        return Uninitialized()
    if "Header" in obj:
        val = obj["Header"]
        return Header((audit_log_header.AuditLogHeader.from_decoded(val["item_0"]),))
    if "Fill" in obj:
        val = obj["Fill"]
        return Fill((fill_event.FillEvent.from_decoded(val["item_0"]),))
    if "Place" in obj:
        val = obj["Place"]
        return Place((place_event.PlaceEvent.from_decoded(val["item_0"]),))
    if "Reduce" in obj:
        val = obj["Reduce"]
        return Reduce((reduce_event.ReduceEvent.from_decoded(val["item_0"]),))
    if "Evict" in obj:
        val = obj["Evict"]
        return Evict((evict_event.EvictEvent.from_decoded(val["item_0"]),))
    if "FillSummary" in obj:
        val = obj["FillSummary"]
        return FillSummary(
            (fill_summary_event.FillSummaryEvent.from_decoded(val["item_0"]),)
        )
    if "Fee" in obj:
        val = obj["Fee"]
        return Fee((fee_event.FeeEvent.from_decoded(val["item_0"]),))
    if "TimeInForce" in obj:
        val = obj["TimeInForce"]
        return TimeInForce(
            (time_in_force_event.TimeInForceEvent.from_decoded(val["item_0"]),)
        )
    if "ExpiredOrder" in obj:
        val = obj["ExpiredOrder"]
        return ExpiredOrder(
            (expired_order_event.ExpiredOrderEvent.from_decoded(val["item_0"]),)
        )
    raise ValueError("Invalid enum object")


def from_json(obj: PhoenixMarketEventJSON) -> PhoenixMarketEventKind:
    if obj["kind"] == "Uninitialized":
        return Uninitialized()
    if obj["kind"] == "Header":
        header_json_value = typing.cast(HeaderJSONValue, obj["value"])
        return Header(
            (audit_log_header.AuditLogHeader.from_json(header_json_value[0]),)
        )
    if obj["kind"] == "Fill":
        fill_json_value = typing.cast(FillJSONValue, obj["value"])
        return Fill((fill_event.FillEvent.from_json(fill_json_value[0]),))
    if obj["kind"] == "Place":
        place_json_value = typing.cast(PlaceJSONValue, obj["value"])
        return Place((place_event.PlaceEvent.from_json(place_json_value[0]),))
    if obj["kind"] == "Reduce":
        reduce_json_value = typing.cast(ReduceJSONValue, obj["value"])
        return Reduce((reduce_event.ReduceEvent.from_json(reduce_json_value[0]),))
    if obj["kind"] == "Evict":
        evict_json_value = typing.cast(EvictJSONValue, obj["value"])
        return Evict((evict_event.EvictEvent.from_json(evict_json_value[0]),))
    if obj["kind"] == "FillSummary":
        fill_summary_json_value = typing.cast(FillSummaryJSONValue, obj["value"])
        return FillSummary(
            (fill_summary_event.FillSummaryEvent.from_json(fill_summary_json_value[0]),)
        )
    if obj["kind"] == "Fee":
        fee_json_value = typing.cast(FeeJSONValue, obj["value"])
        return Fee((fee_event.FeeEvent.from_json(fee_json_value[0]),))
    if obj["kind"] == "TimeInForce":
        time_in_force_json_value = typing.cast(TimeInForceJSONValue, obj["value"])
        return TimeInForce(
            (
                time_in_force_event.TimeInForceEvent.from_json(
                    time_in_force_json_value[0]
                ),
            )
        )
    if obj["kind"] == "ExpiredOrder":
        expired_order_json_value = typing.cast(ExpiredOrderJSONValue, obj["value"])
        return ExpiredOrder(
            (
                expired_order_event.ExpiredOrderEvent.from_json(
                    expired_order_json_value[0]
                ),
            )
        )
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Uninitialized" / borsh.CStruct(),
    "Header" / borsh.CStruct("item_0" / audit_log_header.AuditLogHeader.layout),
    "Fill" / borsh.CStruct("item_0" / fill_event.FillEvent.layout),
    "Place" / borsh.CStruct("item_0" / place_event.PlaceEvent.layout),
    "Reduce" / borsh.CStruct("item_0" / reduce_event.ReduceEvent.layout),
    "Evict" / borsh.CStruct("item_0" / evict_event.EvictEvent.layout),
    "FillSummary"
    / borsh.CStruct("item_0" / fill_summary_event.FillSummaryEvent.layout),
    "Fee" / borsh.CStruct("item_0" / fee_event.FeeEvent.layout),
    "TimeInForce"
    / borsh.CStruct("item_0" / time_in_force_event.TimeInForceEvent.layout),
    "ExpiredOrder"
    / borsh.CStruct("item_0" / expired_order_event.ExpiredOrderEvent.layout),
)
