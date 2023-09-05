from phoenix.market import Market
import asyncio
import os
from solders.pubkey import Pubkey
from asyncstdlib import enumerate
from solana.rpc.websocket_api import connect


async def main():
    solusdc_market_pubkey = Pubkey.from_string(
        "4DoNfFBfF7UokCC2FQzriy7yHK6DY6NVdYpuekQ5pRgg"
    )
    async with connect("wss://api.mainnet-beta.solana.com") as websocket:
        await websocket.account_subscribe(
            solusdc_market_pubkey, "confirmed", "base64+zstd"
        )
        first_resp = await websocket.recv()
        subscription_id = first_resp[0].result
        async for _, msg in enumerate(websocket):
            try:
                market = Market.deserialize_market_data(
                    solusdc_market_pubkey, msg[0].result.value.data
                )
                os.system("clear")
                print(market.get_ui_ladder())
            except Exception as e:
                print(f"WARNING: Failed to parse message: {e}")
        await websocket.account_unsubscribe(subscription_id)


asyncio.run(main())
