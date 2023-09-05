import base58
import struct
from typing import List, Optional
from phoenix.program_id import PROGRAM_ID
from phoenix.types.audit_log_header import AuditLogHeader
from phoenix.types.fill_summary_event import FillSummaryEvent
from phoenix.types.phoenix_market_event import PhoenixMarketEventKind, from_decoded
from phoenix.types.phoenix_market_event import layout as phoenix_market_event_layout
from phoenix.types.place_event import PlaceEvent
from phoenix.types.reduce_event import ReduceEvent
from phoenix.types.evict_event import EvictEvent
from phoenix.types.expired_order_event import ExpiredOrderEvent
from phoenix.types.fee_event import FeeEvent
from phoenix.types.time_in_force_event import TimeInForceEvent
from phoenix.types.fill_event import FillEvent
from solders.transaction_status import EncodedConfirmedTransactionWithStatusMeta
from solders.pubkey import Pubkey

LOG_INSTRUCTION_DISCRIMINATOR = 15


class PhoenixEventsFromInstruction:
    def __init__(self, header: AuditLogHeader, events: List[PhoenixMarketEventKind]):
        self.header = header
        self.events = events


class PhoenixTransaction:
    def __init__(
        self,
        events_from_instructions: List[PhoenixEventsFromInstruction],
        signature: Optional[str] = None,
        txReceived: bool = False,
        txFailed: bool = False,
    ):
        self.events_from_instructions = events_from_instructions
        self.signature = signature
        self.txReceived = txReceived
        self.txFailed = txFailed


class PhoenixEvents:
    def __init__(self, events: List[PhoenixMarketEventKind]):
        self.events = events


def get_phoenix_events_from_confirmed_transaction_with_meta(
    tx_data: EncodedConfirmedTransactionWithStatusMeta,
) -> PhoenixTransaction:
    meta = tx_data.transaction.meta

    if not meta:
        return PhoenixTransaction([], txReceived=False, txFailed=True)

    if meta.err is not None:
        return PhoenixTransaction([], txReceived=True, txFailed=True)

    inner_ixs = meta.inner_instructions
    if not inner_ixs or not tx_data.transaction or not tx_data.slot:
        return PhoenixTransaction([], txReceived=True, txFailed=True)

    data_array: List[bytes] = []

    for ix in inner_ixs:
        for inner in ix.instructions:
            if (
                tx_data.transaction.transaction.message.account_keys[
                    inner.program_id_index
                ]
                != PROGRAM_ID
            ):
                continue
            raw_data = base58.b58decode(inner.data)
            if raw_data[0] == LOG_INSTRUCTION_DISCRIMINATOR:
                data_array.append(raw_data[1:])

    instructions = [get_phoenix_events_from_log_data(data) for data in data_array]

    return PhoenixTransaction(
        instructions,
        signature=tx_data.transaction.transaction.signatures[0],
        txReceived=True,
        txFailed=False,
    )


def get_phoenix_events_from_log_data(data: bytes) -> PhoenixEventsFromInstruction:
    reader_index = 0

    # Read the first byte
    # A byte of 1 identifies a header event
    (byte,) = struct.unpack_from("B", data, reader_index)
    reader_index += 1
    if byte != 1:
        raise Exception("early Unexpected event")

    header = AuditLogHeader.layout.parse(data[reader_index:])
    # Create the length buffer
    length_buffer = struct.pack("I", header.total_events)
    # Coerce the buffer for Borsh-encoded vector decoding
    events_data = length_buffer + data[AuditLogHeader.layout.sizeof() + 1 :]

    events = decode_phoenix_events(events_data)

    return PhoenixEventsFromInstruction(header, events)


EVENT_CLASSES = {
    "Uninitialized": None,  # No event class for "Uninitialized"
    "Header": AuditLogHeader,
    "Fill": FillEvent,
    "Place": PlaceEvent,
    "Reduce": ReduceEvent,
    "Evict": EvictEvent,
    "FillSummary": FillSummaryEvent,
    "Fee": FeeEvent,
    "TimeInForce": TimeInForceEvent,
    "ExpiredOrder": ExpiredOrderEvent,
}


def decode_phoenix_events(data: bytes) -> List[PhoenixMarketEventKind]:
    # Decode the length of the events array
    num_of_events = int.from_bytes(data[:4], "little")
    offset = 4
    events = []

    while offset < len(data):
        # Deserializing each event based on the layout
        event = phoenix_market_event_layout.parse(data[offset:])
        # Get the corresponding class, parse and adjust the offset
        event_type = list(event.keys())[0]
        event_class = EVENT_CLASSES[event_type]
        event_instance = from_decoded(event)
        events.append(event_instance)
        event_size = event_class.layout.sizeof() + 1
        offset += event_size
    assert (
        len(events) == num_of_events
    ), "Decoding events from transaction: Mismatch in event length"

    return events


def read_public_key(data: bytes) -> Pubkey:
    # Extract the 32 bytes for the public key
    pubkey_bytes = data[:32]

    # Convert the bytes to a Pubkey
    pubkey = Pubkey.from_bytes(pubkey_bytes)

    return pubkey
