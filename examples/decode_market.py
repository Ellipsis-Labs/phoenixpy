from phoenix.client import PhoenixClient
import asyncio
from solders.pubkey import Pubkey


async def main():
    client = PhoenixClient()
    solusdc_market_pubkey = Pubkey.from_string(
        "4DoNfFBfF7UokCC2FQzriy7yHK6DY6NVdYpuekQ5pRgg"
    )
    print(await client.get_l2_book(solusdc_market_pubkey))
    await client.close()


asyncio.run(main())
