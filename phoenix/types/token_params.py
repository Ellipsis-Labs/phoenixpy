from __future__ import annotations
import typing
from dataclasses import dataclass
from construct import Container
from solders.pubkey import Pubkey
from anchorpy.borsh_extension import BorshPubkey
import borsh_construct as borsh


class TokenParamsJSON(typing.TypedDict):
    decimals: int
    vault_bump: int
    mint_key: str
    vault_key: str


@dataclass
class TokenParams:
    layout: typing.ClassVar = borsh.CStruct(
        "decimals" / borsh.U32,
        "vault_bump" / borsh.U32,
        "mint_key" / BorshPubkey,
        "vault_key" / BorshPubkey,
    )
    decimals: int
    vault_bump: int
    mint_key: Pubkey
    vault_key: Pubkey

    @classmethod
    def from_decoded(cls, obj: Container) -> "TokenParams":
        return cls(
            decimals=obj.decimals,
            vault_bump=obj.vault_bump,
            mint_key=obj.mint_key,
            vault_key=obj.vault_key,
        )

    def to_encodable(self) -> dict[str, typing.Any]:
        return {
            "decimals": self.decimals,
            "vault_bump": self.vault_bump,
            "mint_key": self.mint_key,
            "vault_key": self.vault_key,
        }

    def to_json(self) -> TokenParamsJSON:
        return {
            "decimals": self.decimals,
            "vault_bump": self.vault_bump,
            "mint_key": str(self.mint_key),
            "vault_key": str(self.vault_key),
        }

    @classmethod
    def from_json(cls, obj: TokenParamsJSON) -> "TokenParams":
        return cls(
            decimals=obj["decimals"],
            vault_bump=obj["vault_bump"],
            mint_key=Pubkey.from_string(obj["mint_key"]),
            vault_key=Pubkey.from_string(obj["vault_key"]),
        )
