from phoenix.events import get_phoenix_events_from_confirmed_transaction_with_meta
from phoenix.client import PhoenixClient
import asyncio
from solders.signature import Signature


async def main():
    client = PhoenixClient()
    signature = Signature.from_string(
        "2Lqa743RivAoaZCd6mFWyedQQ8jmCWUESVkP8nEVAuH1xG5khakTg2entgcFp58QC5gbs5tfKigUwi3uaEFomQ3K"
    )
    transaction_response = await client.client.get_transaction(
        signature, "json", "confirmed"
    )
    print(transaction_response.value)
    phoenix_transaction = get_phoenix_events_from_confirmed_transaction_with_meta(
        transaction_response.value
    )

    for ix_events in phoenix_transaction.events_from_instructions:
        for phoenix_event in ix_events.events:
            print(phoenix_event)
    await client.close()


asyncio.run(main())
