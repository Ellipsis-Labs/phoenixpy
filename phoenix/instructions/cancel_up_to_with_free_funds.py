from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class CancelUpToWithFreeFundsArgs(typing.TypedDict):
    params: types.cancel_up_to_params.CancelUpToParams


layout = borsh.CStruct("params" / types.cancel_up_to_params.CancelUpToParams.layout)


class CancelUpToWithFreeFundsAccounts(typing.TypedDict):
    phoenix_program: Pubkey
    log_authority: Pubkey
    market: Pubkey
    trader: Pubkey


def cancel_up_to_with_free_funds(
    args: CancelUpToWithFreeFundsArgs,
    accounts: CancelUpToWithFreeFundsAccounts,
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
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x09"
    encoded_args = layout.build(
        {
            "params": args["params"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
