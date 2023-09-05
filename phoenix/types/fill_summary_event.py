from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
import borsh_construct as borsh


class FillSummaryEventJSON(typing.TypedDict):
    index: int
    client_order_id: int
    total_base_lots_filled: int
    total_quote_lots_filled: int
    total_fee_in_quote_lots: int


@dataclass
class FillSummaryEvent:
    layout: typing.ClassVar = borsh.CStruct(
        "index" / borsh.U16,
        "client_order_id" / borsh.U128,
        "total_base_lots_filled" / borsh.U64,
        "total_quote_lots_filled" / borsh.U64,
        "total_fee_in_quote_lots" / borsh.U64,
    )
    index: int
    client_order_id: int
    total_base_lots_filled: int
    total_quote_lots_filled: int
    total_fee_in_quote_lots: int

    @classmethod
    def from_decoded(cls, obj: Container) -> "FillSummaryEvent":
        return cls(
            index=obj.index,
            client_order_id=obj.client_order_id,
            total_base_lots_filled=obj.total_base_lots_filled,
            total_quote_lots_filled=obj.total_quote_lots_filled,
            total_fee_in_quote_lots=obj.total_fee_in_quote_lots,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "index": self.index,
            "client_order_id": self.client_order_id,
            "total_base_lots_filled": self.total_base_lots_filled,
            "total_quote_lots_filled": self.total_quote_lots_filled,
            "total_fee_in_quote_lots": self.total_fee_in_quote_lots,
        }

    def to_json(self) -> FillSummaryEventJSON:
        return {
            "index": self.index,
            "client_order_id": self.client_order_id,
            "total_base_lots_filled": self.total_base_lots_filled,
            "total_quote_lots_filled": self.total_quote_lots_filled,
            "total_fee_in_quote_lots": self.total_fee_in_quote_lots,
        }

    @classmethod
    def from_json(cls, obj: FillSummaryEventJSON) -> "FillSummaryEvent":
        return cls(
            index=obj["index"],
            client_order_id=obj["client_order_id"],
            total_base_lots_filled=obj["total_base_lots_filled"],
            total_quote_lots_filled=obj["total_quote_lots_filled"],
            total_fee_in_quote_lots=obj["total_fee_in_quote_lots"],
        )
