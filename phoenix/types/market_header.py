from __future__ import annotations
from . import (
    market_size_params,
    token_params,
)
import typing
from dataclasses import dataclass
from construct import Container
from solders.pubkey import Pubkey
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh

MARKET_HEADER_SIZE = 576


class MarketHeaderJSON(typing.TypedDict):
    discriminant: int
    status: int
    market_size_params: market_size_params.MarketSizeParamsJSON
    base_params: token_params.TokenParamsJSON
    base_lot_size: int
    quote_params: token_params.TokenParamsJSON
    quote_lot_size: int
    tick_size_in_quote_atoms_per_base_unit: int
    authority: str
    fee_recipient: str
    market_sequence_number: int
    successor: str
    raw_base_units_per_base_unit: int
    padding1: int
    padding2: list[int]


@dataclass
class MarketHeader:
    layout: typing.ClassVar = borsh.CStruct(
        "discriminant" / borsh.U64,
        "status" / borsh.U64,
        "market_size_params" / market_size_params.MarketSizeParams.layout,
        "base_params" / token_params.TokenParams.layout,
        "base_lot_size" / borsh.U64,
        "quote_params" / token_params.TokenParams.layout,
        "quote_lot_size" / borsh.U64,
        "tick_size_in_quote_atoms_per_base_unit" / borsh.U64,
        "authority" / BorshPubkey,
        "fee_recipient" / BorshPubkey,
        "market_sequence_number" / borsh.U64,
        "successor" / BorshPubkey,
        "raw_base_units_per_base_unit" / borsh.U32,
        "padding1" / borsh.U32,
        "padding2" / borsh.U64[32],
    )
    discriminant: int
    status: int
    market_size_params: market_size_params.MarketSizeParams
    base_params: token_params.TokenParams
    base_lot_size: int
    quote_params: token_params.TokenParams
    quote_lot_size: int
    tick_size_in_quote_atoms_per_base_unit: int
    authority: Pubkey
    fee_recipient: Pubkey
    market_sequence_number: int
    successor: Pubkey
    raw_base_units_per_base_unit: int
    padding1: int
    padding2: list[int]

    @classmethod
    def from_decoded(cls, obj: Container) -> "MarketHeader":
        return cls(
            discriminant=obj.discriminant,
            status=obj.status,
            market_size_params=market_size_params.MarketSizeParams.from_decoded(
                obj.market_size_params
            ),
            base_params=token_params.TokenParams.from_decoded(obj.base_params),
            base_lot_size=obj.base_lot_size,
            quote_params=token_params.TokenParams.from_decoded(obj.quote_params),
            quote_lot_size=obj.quote_lot_size,
            tick_size_in_quote_atoms_per_base_unit=obj.tick_size_in_quote_atoms_per_base_unit,
            authority=obj.authority,
            fee_recipient=obj.fee_recipient,
            market_sequence_number=obj.market_sequence_number,
            successor=obj.successor,
            raw_base_units_per_base_unit=obj.raw_base_units_per_base_unit,
            padding1=obj.padding1,
            padding2=obj.padding2,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "discriminant": self.discriminant,
            "status": self.status,
            "market_size_params": self.market_size_params.to_encodable(),
            "base_params": self.base_params.to_encodable(),
            "base_lot_size": self.base_lot_size,
            "quote_params": self.quote_params.to_encodable(),
            "quote_lot_size": self.quote_lot_size,
            "tick_size_in_quote_atoms_per_base_unit": self.tick_size_in_quote_atoms_per_base_unit,
            "authority": self.authority,
            "fee_recipient": self.fee_recipient,
            "market_sequence_number": self.market_sequence_number,
            "successor": self.successor,
            "raw_base_units_per_base_unit": self.raw_base_units_per_base_unit,
            "padding1": self.padding1,
            "padding2": self.padding2,
        }

    def to_json(self) -> MarketHeaderJSON:
        return {
            "discriminant": self.discriminant,
            "status": self.status,
            "market_size_params": self.market_size_params.to_json(),
            "base_params": self.base_params.to_json(),
            "base_lot_size": self.base_lot_size,
            "quote_params": self.quote_params.to_json(),
            "quote_lot_size": self.quote_lot_size,
            "tick_size_in_quote_atoms_per_base_unit": self.tick_size_in_quote_atoms_per_base_unit,
            "authority": str(self.authority),
            "fee_recipient": str(self.fee_recipient),
            "market_sequence_number": self.market_sequence_number,
            "successor": str(self.successor),
            "raw_base_units_per_base_unit": self.raw_base_units_per_base_unit,
            "padding1": self.padding1,
            "padding2": self.padding2,
        }

    @classmethod
    def from_json(cls, obj: MarketHeaderJSON) -> "MarketHeader":
        return cls(
            discriminant=obj["discriminant"],
            status=obj["status"],
            market_size_params=market_size_params.MarketSizeParams.from_json(
                obj["market_size_params"]
            ),
            base_params=token_params.TokenParams.from_json(obj["base_params"]),
            base_lot_size=obj["base_lot_size"],
            quote_params=token_params.TokenParams.from_json(obj["quote_params"]),
            quote_lot_size=obj["quote_lot_size"],
            tick_size_in_quote_atoms_per_base_unit=obj[
                "tick_size_in_quote_atoms_per_base_unit"
            ],
            authority=Pubkey.from_string(obj["authority"]),
            fee_recipient=Pubkey.from_string(obj["fee_recipient"]),
            market_sequence_number=obj["market_sequence_number"],
            successor=Pubkey.from_string(obj["successor"]),
            raw_base_units_per_base_unit=obj["raw_base_units_per_base_unit"],
            padding1=obj["padding1"],
            padding2=obj["padding2"],
        )
