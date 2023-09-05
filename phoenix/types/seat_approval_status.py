from __future__ import annotations
import typing
from dataclasses import dataclass
from anchorpy.borsh_extension import EnumForCodegen
import borsh_construct as borsh


class NotApprovedJSON(typing.TypedDict):
    kind: typing.Literal["NotApproved"]


class ApprovedJSON(typing.TypedDict):
    kind: typing.Literal["Approved"]


class RetiredJSON(typing.TypedDict):
    kind: typing.Literal["Retired"]


@dataclass
class NotApproved:
    discriminator: typing.ClassVar = 0
    kind: typing.ClassVar = "NotApproved"

    @classmethod
    def to_json(cls) -> NotApprovedJSON:
        return NotApprovedJSON(
            kind="NotApproved",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "NotApproved": {},
        }


@dataclass
class Approved:
    discriminator: typing.ClassVar = 1
    kind: typing.ClassVar = "Approved"

    @classmethod
    def to_json(cls) -> ApprovedJSON:
        return ApprovedJSON(
            kind="Approved",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Approved": {},
        }


@dataclass
class Retired:
    discriminator: typing.ClassVar = 2
    kind: typing.ClassVar = "Retired"

    @classmethod
    def to_json(cls) -> RetiredJSON:
        return RetiredJSON(
            kind="Retired",
        )

    @classmethod
    def to_encodable(cls) -> dict:
        return {
            "Retired": {},
        }


SeatApprovalStatusKind = typing.Union[NotApproved, Approved, Retired]
SeatApprovalStatusJSON = typing.Union[NotApprovedJSON, ApprovedJSON, RetiredJSON]


def from_decoded(obj: dict) -> SeatApprovalStatusKind:
    if not isinstance(obj, dict):
        raise ValueError("Invalid enum object")
    if "NotApproved" in obj:
        return NotApproved()
    if "Approved" in obj:
        return Approved()
    if "Retired" in obj:
        return Retired()
    raise ValueError("Invalid enum object")


def from_json(obj: SeatApprovalStatusJSON) -> SeatApprovalStatusKind:
    if obj["kind"] == "NotApproved":
        return NotApproved()
    if obj["kind"] == "Approved":
        return Approved()
    if obj["kind"] == "Retired":
        return Retired()
    kind = obj["kind"]
    raise ValueError(f"Unrecognized enum kind: {kind}")


layout = EnumForCodegen(
    "NotApproved" / borsh.CStruct(),
    "Approved" / borsh.CStruct(),
    "Retired" / borsh.CStruct(),
)
