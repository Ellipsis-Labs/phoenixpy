from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
from solders.pubkey import Pubkey
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh


class AuditLogHeaderJSON(typing.TypedDict):
    instruction: int
    sequence_number: int
    timestamp: int
    slot: int
    market: str
    signer: str
    total_events: int


@dataclass
class AuditLogHeader:
    layout: typing.ClassVar = borsh.CStruct(
        "instruction" / borsh.U8,
        "sequence_number" / borsh.U64,
        "timestamp" / borsh.I64,
        "slot" / borsh.U64,
        "market" / BorshPubkey,
        "signer" / BorshPubkey,
        "total_events" / borsh.U16,
    )
    instruction: int
    sequence_number: int
    timestamp: int
    slot: int
    market: Pubkey
    signer: Pubkey
    total_events: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "AuditLogHeader":
        return cls(
            instruction=obj.instruction,
            sequence_number=obj.sequence_number,
            timestamp=obj.timestamp,
            slot=obj.slot,
            market=obj.market,
            signer=obj.signer,
            total_events=obj.total_events,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "instruction": self.instruction,
            "sequence_number": self.sequence_number,
            "timestamp": self.timestamp,
            "slot": self.slot,
            "market": self.market,
            "signer": self.signer,
            "total_events": self.total_events,
        }

    def to_json(self) -> AuditLogHeaderJSON:
        return {
            "instruction": self.instruction,
            "sequence_number": self.sequence_number,
            "timestamp": self.timestamp,
            "slot": self.slot,
            "market": str(self.market),
            "signer": str(self.signer),
            "total_events": self.total_events,
        }

    @classmethod
    def from_json(cls, obj: AuditLogHeaderJSON) -> "AuditLogHeader":
        return cls(
            instruction=obj["instruction"],
            sequence_number=obj["sequence_number"],
            timestamp=obj["timestamp"],
            slot=obj["slot"],
            market=Pubkey.from_string(obj["market"]),
            signer=Pubkey.from_string(obj["signer"]),
            total_events=obj["total_events"],
        )
