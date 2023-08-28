from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class DepositFundsArgs(typing.TypedDict):
    deposit_funds_params: types.deposit_params.DepositParams


layout = borsh.CStruct(
    "deposit_funds_params" / types.deposit_params.DepositParams.layout
)


class DepositFundsAccounts(typing.TypedDict):
    phoenix_program: Pubkey
    log_authority: Pubkey
    market: Pubkey
    trader: Pubkey
    seat: Pubkey
    base_account: Pubkey
    quote_account: Pubkey
    base_vault: Pubkey
    quote_vault: Pubkey


def deposit_funds(
    args: DepositFundsArgs,
    accounts: DepositFundsAccounts,
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
        AccountMeta(pubkey=accounts["seat"], is_signer=False, is_writable=False),
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
    identifier = b"\x0d"
    encoded_args = layout.build(
        {
            "deposit_funds_params": args["deposit_funds_params"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
