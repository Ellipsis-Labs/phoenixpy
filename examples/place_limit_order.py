import asyncio
import os
import json

from solana.rpc.types import TxOpts
import requests
from phoenix.client import PhoenixClient
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from phoenix.types.side import Ask, Bid


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

    # make a request to the SOL-USD market on coinbase and fetch the price

    price = float(
        requests.get("https://api.pro.coinbase.com/products/SOL-USD/ticker").json()[
            "price"
        ]
    )

    # Create order packets for the given market
    limit_order_packet = client.get_limit_order_packet(
        solusdc_market_pubkey, Bid, price * 0.98, 0.01
    )
    limit_order_packet_two = client.get_limit_order_packet(
        solusdc_market_pubkey, Bid, price * 0.97, 0.01
    )
    limit_order_packet_three = client.get_limit_order_packet(
        solusdc_market_pubkey, Ask, price * 1.03, 0.01
    )

    # Execute order packets; returns a map of client_order_id to FIFOOrderId of orders that were executed
    order_ids_map = await client.send_orders(
        signer,
        [limit_order_packet, limit_order_packet_two, limit_order_packet_three],
        tx_opts=TxOpts(skip_preflight=True),
    )
    print("Order Id Map: ", order_ids_map)

    orders_to_cancel = list(
        map(lambda x: x.order_id, order_ids_map.client_orders_map.values())
    )
    print("Order IDs to cancel (numeric): ", orders_to_cancel)

    print(
        "All orders",
        await client.get_active_orders(
            market_pubkey=solusdc_market_pubkey, trader_pubkey=signer.pubkey()
        ),
    )
    print(
        "Bid orders",
        await client.get_active_orders(
            market_pubkey=solusdc_market_pubkey,
            trader_pubkey=signer.pubkey(),
            side="bid",
        ),
    )
    print(
        "Ask orders",
        await client.get_active_orders(
            market_pubkey=solusdc_market_pubkey,
            trader_pubkey=signer.pubkey(),
            side="ask",
        ),
    )

    # Cancel orders
    cancelled_orders = await client.cancel_orders(
        signer,
        solusdc_market_pubkey,
        orders_to_cancel,
    )

    print("Cancelled orders: ", cancelled_orders)

    # Cancel all orders
    print("Cancelling all orders")
    cancelled_orders = await client.cancel_all_orders(
        signer,
        solusdc_market_pubkey,
    )
    print("Cancelled orders: ", cancelled_orders)

    await client.close()


asyncio.run(main())
