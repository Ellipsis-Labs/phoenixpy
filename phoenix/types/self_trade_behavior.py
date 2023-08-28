from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class AbortJSON(typing.TypedDict):
    kind: typing.Literal["Abort"]


class CancelProvideJSON(typing.TypedDict):
    kind: typing.Literal["CancelProvide"]


class DecrementTakeJSON(typing.TypedDict):
    kind: typing.Literal["DecrementTake"]


@dataclass
class Abort:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "Abort"

    @classmethod
    def to_json(cls) -> AbortJSON:
        return AbortJSON(
            kind="Abort",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Abort": {},
        }


@dataclass
class CancelProvide:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "CancelProvide"

    @classmethod
    def to_json(cls) -> CancelProvideJSON:
        return CancelProvideJSON(
            kind="CancelProvide",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "CancelProvide": {},
        }


@dataclass
class DecrementTake:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "DecrementTake"

    @classmethod
    def to_json(cls) -> DecrementTakeJSON:
        return DecrementTakeJSON(
            kind="DecrementTake",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "DecrementTake": {},
        }


SelfTradeBehaviorKind = typing.Union[Abort, CancelProvide, DecrementTake]
SelfTradeBehaviorJSON = typing.Union[AbortJSON, CancelProvideJSON, DecrementTakeJSON]


def from_decoded(obj: dict) -> SelfTradeBehaviorKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "Abort" in obj:
        return Abort()
    if "CancelProvide" in obj:
        return CancelProvide()
    if "DecrementTake" in obj:
        return DecrementTake()
    raise ValueError("Invalid enum object")


def from_json(obj: SelfTradeBehaviorJSON) -> SelfTradeBehaviorKind:
    if obj["kind"] == "Abort":
        return Abort()
    if obj["kind"] == "CancelProvide":
        return CancelProvide()
    if obj["kind"] == "DecrementTake":
        return DecrementTake()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "Abort" / borsh.CStruct(),
    "CancelProvide" / borsh.CStruct(),
    "DecrementTake" / borsh.CStruct(),
)
