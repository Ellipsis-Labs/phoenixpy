from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class UninitializedJSON(typing.TypedDict):
    kind: typing.Literal["Uninitialized"]


class ActiveJSON(typing.TypedDict):
    kind: typing.Literal["Active"]


class PostOnlyJSON(typing.TypedDict):
    kind: typing.Literal["PostOnly"]


class PausedJSON(typing.TypedDict):
    kind: typing.Literal["Paused"]


class ClosedJSON(typing.TypedDict):
    kind: typing.Literal["Closed"]


class TombstonedJSON(typing.TypedDict):
    kind: typing.Literal["Tombstoned"]


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
class Active:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Active"

    @classmethod
    def to_json(cls) -> ActiveJSON:
        return ActiveJSON(
            kind="Active",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Active": {},
        }


@dataclass
class PostOnly:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "PostOnly"

    @classmethod
    def to_json(cls) -> PostOnlyJSON:
        return PostOnlyJSON(
            kind="PostOnly",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "PostOnly": {},
        }


@dataclass
class Paused:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "Paused"

    @classmethod
    def to_json(cls) -> PausedJSON:
        return PausedJSON(
            kind="Paused",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Paused": {},
        }


@dataclass
class Closed:
    discriminator: typing.ClassVar = 4
    kind: typing.ClassVar = "Closed"

    @classmethod
    def to_json(cls) -> ClosedJSON:
        return ClosedJSON(
            kind="Closed",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Closed": {},
        }


@dataclass
class Tombstoned:
    discriminator: typing.ClassVar = 5
    kind: typing.ClassVar = "Tombstoned"

    @classmethod
    def to_json(cls) -> TombstonedJSON:
        return TombstonedJSON(
            kind="Tombstoned",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Tombstoned": {},
        }


MarketStatusKind = typing.Union[
    Uninitialized, Active, PostOnly, Paused, Closed, Tombstoned
]
MarketStatusJSON = typing.Union[
    UninitializedJSON, ActiveJSON, PostOnlyJSON, PausedJSON, ClosedJSON, TombstonedJSON
]


def from_decoded(obj: dict) -> MarketStatusKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Uninitialized" in obj:
        return Uninitialized()
    if "Active" in obj:
        return Active()
    if "PostOnly" in obj:
        return PostOnly()
    if "Paused" in obj:
        return Paused()
    if "Closed" in obj:
        return Closed()
    if "Tombstoned" in obj:
        return Tombstoned()
    raise ValueError("Invalid enum object")


def from_json(obj: MarketStatusJSON) -> MarketStatusKind:
    if obj["kind"] == "Uninitialized":
        return Uninitialized()
    if obj["kind"] == "Active":
        return Active()
    if obj["kind"] == "PostOnly":
        return PostOnly()
    if obj["kind"] == "Paused":
        return Paused()
    if obj["kind"] == "Closed":
        return Closed()
    if obj["kind"] == "Tombstoned":
        return Tombstoned()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Uninitialized" / borsh.CStruct(),
    "Active" / borsh.CStruct(),
    "PostOnly" / borsh.CStruct(),
    "Paused" / borsh.CStruct(),
    "Closed" / borsh.CStruct(),
    "Tombstoned" / borsh.CStruct(),
)
