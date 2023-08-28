import datetime
from construct import Optional
from solana.rpc.commitment import Commitment
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

from .market import DEFAULT_L2_LADDER_DEPTH, Market


class PhoenixClient:
    def __init__(
        self,
        endpoint="api.mainnet-beta.solana.com",
        custom_url=None,
        custom_ws_url=None,
        commitment: Commitment = "confirmed",
        encoding: str = "base64+zstd",
    ):
        if custom_url is None:
            self.endpoint = f"https://{endpoint.split('://')[-1]}"
        else:
            self.endpoint = custom_url
        self.client = AsyncClient(self.endpoint)

        if custom_ws_url is None:
            self.ws_endpoint = f"wss://{endpoint.split('://')[-1]}"
        else:
            self.ws_endpoint = custom_ws_url

        self.commitment = commitment
        self.encoding = encoding

        self.markets = {}

    async def add_market(self, market_pubkey: Pubkey):
        market_bytes = await self.client.get_account_info(
            market_pubkey, self.commitment, self.encoding
        )
        self.markets[market_pubkey] = Market.deserialize_market_data(
            market_bytes.value.data
        ).metadata

    async def get_l2_book(self, market_pubkey: Pubkey, levels=DEFAULT_L2_LADDER_DEPTH):
        market_account = await self.client.get_account_info(
            market_pubkey, self.commitment, self.encoding
        )
        slot = market_account.context.slot
        market = Market.deserialize_market_data(market_account.value.data)
        unix_timestamp = (await self.client.get_block_time(slot)).value
        return market.get_ui_ladder(slot, unix_timestamp, levels)

    async def close(self):
        await self.client.close()
