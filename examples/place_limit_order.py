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

    client = PhoenixClient(endpoint="https://api.devnet.solana.com")
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

    # TODO: Create method to get a seat on a market

    # Create order packets for the given market
    limit_order_packet = client.get_limit_order_packet(
        solusdc_market_pubkey, Bid, 18, 0.01
    )
    limit_order_packet_two = client.get_limit_order_packet(
        solusdc_market_pubkey, Bid, 19, 0.01
    )

    # Execute order packets; returns a map of client_order_id to FIFOOrderId of orders that were executed
    order_ids_map = await client.send_orders(
        [limit_order_packet, limit_order_packet_two], signer
    )
    print("Order Id Map: ", order_ids_map)

    await client.close()


asyncio.run(main())
