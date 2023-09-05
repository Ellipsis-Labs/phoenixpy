from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class PlaceLimitOrderWithFreeFundsArgs(typing.TypedDict):
    order_packet: types.order_packet.OrderPacketKind


layout = borsh.CStruct("order_packet" / types.order_packet.layout)


class PlaceLimitOrderWithFreeFundsAccounts(typing.TypedDict):
    phoenix_program: Pubkey
    log_authority: Pubkey
    market: Pubkey
    trader: Pubkey
    seat: Pubkey


def place_limit_order_with_free_funds(
    args: PlaceLimitOrderWithFreeFundsArgs,
    accounts: PlaceLimitOrderWithFreeFundsAccounts,
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
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x03"
    encoded_args = layout.build(
        {
            "order_packet": args["order_packet"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
