from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class TimeInForceEventJSON(typing.TypedDict):
    index: int
    order_sequence_number: int
    last_valid_slot: int
    last_valid_unix_timestamp_in_seconds: int


@dataclass
class TimeInForceEvent:
    layout: typing.ClassVar = borsh.CStruct(
        "index" / borsh.U16,
        "order_sequence_number" / borsh.U64,
        "last_valid_slot" / borsh.U64,
        "last_valid_unix_timestamp_in_seconds" / borsh.U64,
    )
    index: int
    order_sequence_number: int
    last_valid_slot: int
    last_valid_unix_timestamp_in_seconds: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "TimeInForceEvent":
        return cls(
            index=obj.index,
            order_sequence_number=obj.order_sequence_number,
            last_valid_slot=obj.last_valid_slot,
            last_valid_unix_timestamp_in_seconds=obj.last_valid_unix_timestamp_in_seconds,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "index": self.index,
            "order_sequence_number": self.order_sequence_number,
            "last_valid_slot": self.last_valid_slot,
            "last_valid_unix_timestamp_in_seconds": self.last_valid_unix_timestamp_in_seconds,
        }

    def to_json(self) -> TimeInForceEventJSON:
        return {
            "index": self.index,
            "order_sequence_number": self.order_sequence_number,
            "last_valid_slot": self.last_valid_slot,
            "last_valid_unix_timestamp_in_seconds": self.last_valid_unix_timestamp_in_seconds,
        }

    @classmethod
    def from_json(cls, obj: TimeInForceEventJSON) -> "TimeInForceEvent":
        return cls(
            index=obj["index"],
            order_sequence_number=obj["order_sequence_number"],
            last_valid_slot=obj["last_valid_slot"],
            last_valid_unix_timestamp_in_seconds=obj[
                "last_valid_unix_timestamp_in_seconds"
            ],
        )
