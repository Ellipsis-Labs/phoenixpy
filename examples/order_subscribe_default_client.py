from phoenix.client import PhoenixClient
import argparse
import asyncio
from solders.pubkey import Pubkey

from phoenix.order_subscribe_response import (
    CancelledOrder,
    FilledOrder,
    OpenOrder,
    OrderSubscribeError,
)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--trader", type=str, help="Trader base58 string")
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        help="URL of Solana cluster",
        default="https://api.mainnet-beta.solana.com",
    )

    args = parser.parse_args()
    market = Pubkey.from_string("4DoNfFBfF7UokCC2FQzriy7yHK6DY6NVdYpuekQ5pRgg")
    trader = Pubkey.from_string(args.trader)
    url = args.url

    client = PhoenixClient(
        endpoint=url,
    )
    async for event_packet in client.order_subscribe_with_default_client(
        market, trader
    ):
        for event in event_packet:
            if isinstance(event, OpenOrder):
                print("place", event)
            if isinstance(event, FilledOrder):
                print("fill", event)
            if isinstance(event, CancelledOrder):
                print("cancel", event)
            if isinstance(event, OrderSubscribeError):
                print("error", event)


asyncio.run(main())
