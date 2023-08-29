import asyncio
import os
import json
from phoenix.market import Market
from phoenix.client import PhoenixClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from phoenix.types.side import Bid


async def main():
    keypair_path = "~/.config/solana/id.json"
    expanded_path = os.path.expanduser(keypair_path)

    # client = PhoenixClient(endpoint="https://api.devnet.solana.com")
    client = PhoenixClient(
        endpoint="https://ellipsis-develope-cbc0.devnet.rpcpool.com/85e1e606-89fd-47a9-9a91-51ec4df1711a"
    )
    with open(expanded_path, "r") as file:
        byte_array = json.load(file)

    signer = Keypair.from_bytes(byte_array)
    print("Pubkey", signer.pubkey())

    # Request airdrop if you are on devnet and require devnet SOL. Note that this request has rate limits and may fail.
    # await client.client.request_airdrop(
    #     signer.pubkey(), 1000000000, commitment="confirmed"
    # )

    # Add the market to the client. CS2H.. is the devnet SOL/USDC market.
    solusdc_market_pubkey = Pubkey.from_string(
        "CS2H8nbAVVEUHWPF5extCSymqheQdkd4d7thik6eet9N"
    )

    await client.add_market(solusdc_market_pubkey)
    market_metadata = client.markets[solusdc_market_pubkey]

    # TODO: Create method to get a seat on a market

    limit_order_packet = client.get_limit_order_packet(Bid, 18, 0.01, market_metadata)
    limit_order_packet_two = client.get_limit_order_packet(
        Bid, 19, 0.01, market_metadata
    )
    print(limit_order_packet, limit_order_packet_two)

    await client.execute([limit_order_packet, limit_order_packet_two], signer)

    await client.close()


asyncio.run(main())
