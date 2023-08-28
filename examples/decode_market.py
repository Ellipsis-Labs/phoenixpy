from phoenix.types import MarketHeader, MARKET_HEADER_SIZE
from phoenix.market import Market
import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey


async def main():
    client = AsyncClient("https://api.mainnet-beta.solana.com")
    solusdc_market_pubkey = Pubkey.from_string(
        "4DoNfFBfF7UokCC2FQzriy7yHK6DY6NVdYpuekQ5pRgg"
    )
    market_bytes = await client.get_account_info(
        solusdc_market_pubkey, "confirmed", "base64+zstd"
    )

    market = Market.deserialize_market_data(market_bytes.value.data)

    print(market.get_ui_ladder())
    await client.close()


asyncio.run(main())
