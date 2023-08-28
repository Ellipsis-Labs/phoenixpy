from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class FailOnInsufficientFundsAndAmendOnCrossJSON(typing.TypedDict):
    kind: typing.Literal["FailOnInsufficientFundsAndAmendOnCross"]


class FailOnInsufficientFundsAndFailOnCrossJSON(typing.TypedDict):
    kind: typing.Literal["FailOnInsufficientFundsAndFailOnCross"]


class SkipOnInsufficientFundsAndAmendOnCrossJSON(typing.TypedDict):
    kind: typing.Literal["SkipOnInsufficientFundsAndAmendOnCross"]


class SkipOnInsufficientFundsAndFailOnCrossJSON(typing.TypedDict):
    kind: typing.Literal["SkipOnInsufficientFundsAndFailOnCross"]


@dataclass
class FailOnInsufficientFundsAndAmendOnCross:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "FailOnInsufficientFundsAndAmendOnCross"

    @classmethod
    def to_json(cls) -> FailOnInsufficientFundsAndAmendOnCrossJSON:
        return FailOnInsufficientFundsAndAmendOnCrossJSON(
            kind="FailOnInsufficientFundsAndAmendOnCross",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "FailOnInsufficientFundsAndAmendOnCross": {},
        }


@dataclass
class FailOnInsufficientFundsAndFailOnCross:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "FailOnInsufficientFundsAndFailOnCross"

    @classmethod
    def to_json(cls) -> FailOnInsufficientFundsAndFailOnCrossJSON:
        return FailOnInsufficientFundsAndFailOnCrossJSON(
            kind="FailOnInsufficientFundsAndFailOnCross",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "FailOnInsufficientFundsAndFailOnCross": {},
        }


@dataclass
class SkipOnInsufficientFundsAndAmendOnCross:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "SkipOnInsufficientFundsAndAmendOnCross"

    @classmethod
    def to_json(cls) -> SkipOnInsufficientFundsAndAmendOnCrossJSON:
        return SkipOnInsufficientFundsAndAmendOnCrossJSON(
            kind="SkipOnInsufficientFundsAndAmendOnCross",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "SkipOnInsufficientFundsAndAmendOnCross": {},
        }


@dataclass
class SkipOnInsufficientFundsAndFailOnCross:
    discriminator: typing.ClassVar = 3
    kind: typing.ClassVar = "SkipOnInsufficientFundsAndFailOnCross"

    @classmethod
    def to_json(cls) -> SkipOnInsufficientFundsAndFailOnCrossJSON:
        return SkipOnInsufficientFundsAndFailOnCrossJSON(
            kind="SkipOnInsufficientFundsAndFailOnCross",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "SkipOnInsufficientFundsAndFailOnCross": {},
        }


FailedMultipleLimitOrderBehaviorKind = typing.Union[
    FailOnInsufficientFundsAndAmendOnCross,
    FailOnInsufficientFundsAndFailOnCross,
    SkipOnInsufficientFundsAndAmendOnCross,
    SkipOnInsufficientFundsAndFailOnCross,
]
FailedMultipleLimitOrderBehaviorJSON = typing.Union[
    FailOnInsufficientFundsAndAmendOnCrossJSON,
    FailOnInsufficientFundsAndFailOnCrossJSON,
    SkipOnInsufficientFundsAndAmendOnCrossJSON,
    SkipOnInsufficientFundsAndFailOnCrossJSON,
]


def from_decoded(obj: dict) -> FailedMultipleLimitOrderBehaviorKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "FailOnInsufficientFundsAndAmendOnCross" in obj:
        return FailOnInsufficientFundsAndAmendOnCross()
    if "FailOnInsufficientFundsAndFailOnCross" in obj:
        return FailOnInsufficientFundsAndFailOnCross()
    if "SkipOnInsufficientFundsAndAmendOnCross" in obj:
        return SkipOnInsufficientFundsAndAmendOnCross()
    if "SkipOnInsufficientFundsAndFailOnCross" in obj:
        return SkipOnInsufficientFundsAndFailOnCross()
    raise ValueError("Invalid enum object")


def from_json(
    obj: FailedMultipleLimitOrderBehaviorJSON,
) -> FailedMultipleLimitOrderBehaviorKind:
    if obj["kind"] == "FailOnInsufficientFundsAndAmendOnCross":
        return FailOnInsufficientFundsAndAmendOnCross()
    if obj["kind"] == "FailOnInsufficientFundsAndFailOnCross":
        return FailOnInsufficientFundsAndFailOnCross()
    if obj["kind"] == "SkipOnInsufficientFundsAndAmendOnCross":
        return SkipOnInsufficientFundsAndAmendOnCross()
    if obj["kind"] == "SkipOnInsufficientFundsAndFailOnCross":
        return SkipOnInsufficientFundsAndFailOnCross()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "FailOnInsufficientFundsAndAmendOnCross" / borsh.CStruct(),
    "FailOnInsufficientFundsAndFailOnCross" / borsh.CStruct(),
    "SkipOnInsufficientFundsAndAmendOnCross" / borsh.CStruct(),
    "SkipOnInsufficientFundsAndFailOnCross" / borsh.CStruct(),
)
