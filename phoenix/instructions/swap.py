from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class SwapArgs(typing.TypedDict):
    order_packet: types.order_packet.OrderPacketKind


layout = borsh.CStruct("order_packet" / types.order_packet.layout)


class SwapAccounts(typing.TypedDict):
    phoenix_program: Pubkey
    log_authority: Pubkey
    market: Pubkey
    trader: Pubkey
    base_account: Pubkey
    quote_account: Pubkey
    base_vault: Pubkey
    quote_vault: Pubkey


def swap(
    args: SwapArgs,
    accounts: SwapAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(
            pubkey=accounts["phoenix_program"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["log_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["market"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["trader"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["base_account"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["quote_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["base_vault"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["quote_vault"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x01"
    encoded_args = layout.build(
        {
            "order_packet": args["order_packet"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
