from phoenix.events import get_phoenix_events_from_confirmed_transaction_with_meta
from phoenix.client import PhoenixClient
import asyncio
from solders.signature import Signature


async def main():
    client = PhoenixClient()
    signature = Signature.from_string(
        "5VvXWNyXpR8mUj393Z77XSkkfRobHQs31dXUF3wD4hVmqoVSpMyevkYrPbR3vv3cpB9BZCp8i4e4e6D6zatCjxQw"
    )
    transaction_response = await client.client.get_transaction(
        signature, "json", "confirmed", 0
    )
    phoenix_transaction = get_phoenix_events_from_confirmed_transaction_with_meta(
        transaction_response.value
    )

    for ix_events in phoenix_transaction.events_from_instructions:
        for phoenix_event in ix_events.events:
            print(phoenix_event)
    await client.close()


asyncio.run(main())
