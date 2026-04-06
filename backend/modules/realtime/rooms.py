from dataclasses import dataclass, field
from fastapi import WebSocket


@dataclass
class Room:
    clients: set[WebSocket] = field(default_factory=set)
    # Accumulated Yjs updates merged into a single binary blob via concatenation.
    # Yjs applies concatenated updates correctly (idempotent CRDT), so this is
    # both correct and far cheaper than storing a list of individual updates.
    doc_state: bytes = b""


rooms: dict[str, Room] = {}

# Minimal valid Yjs v1 update: 0 client-structs + 0 delete-set entries.
_EMPTY_UPDATE = bytes([0, 0])


# ---------------------------------------------------------------------------
# lib0 var-uint helpers (same encoding y-websocket uses for all lengths)
# ---------------------------------------------------------------------------

def _encode_var_uint(value: int) -> bytes:
    result = []
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        result.append(byte)
        if not value:
            break
    return bytes(result)


def _read_var_uint(data: bytes, offset: int) -> tuple[int, int]:
    value = shift = 0
    while offset < len(data):
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
    return value, offset


# ---------------------------------------------------------------------------
# y-websocket message builders
# ---------------------------------------------------------------------------

def build_sync_step1() -> bytes:
    """
    Build a sync step 1 message with an empty state vector.
    Tells the client: "I have nothing — send me your full document state."
    Format: [0 (MSG_SYNC), 0 (STEP_1), <var_uint len>, <state_vector>]
    An empty state vector is encoded as a single 0x00 byte (var-uint 0 clients).
    """
    empty_sv = bytes([0])
    return bytes([0, 0]) + _encode_var_uint(len(empty_sv)) + empty_sv


def make_sync_step2(update: bytes) -> bytes:
    """Wrap a raw Yjs update in a sync step 2 envelope [0, 1, <len>, <update>]."""
    return bytes([0, 1]) + _encode_var_uint(len(update)) + update


def extract_update(data: bytes) -> bytes | None:
    """
    Extract the raw Yjs update bytes from a sync step 2 (type 0x01) or
    sync update (type 0x02) message. Returns None if malformed.
    """
    if len(data) < 3 or data[0] != 0 or data[1] not in (1, 2):
        return None
    length, offset = _read_var_uint(data, 2)
    end = offset + length
    if end > len(data):
        return None
    return data[offset:end]


# ---------------------------------------------------------------------------
# Room operations
# ---------------------------------------------------------------------------

def get_or_create_room(name: str) -> Room:
    if name not in rooms:
        rooms[name] = Room()
    return rooms[name]


def store_update(room: Room, update: bytes) -> None:
    """Merge an incremental Yjs update into the room's accumulated doc state."""
    if update and update != _EMPTY_UPDATE:
        room.doc_state += update


async def send_server_state(ws: WebSocket, room: Room) -> None:
    """
    Send the server's current doc state to a client as a sync step 2 message.
    Receiving this (even the empty variant) causes the y-websocket client to
    set provider.synced = true and emit the 'sync' event.
    """
    if room.doc_state:
        await ws.send_bytes(make_sync_step2(room.doc_state))
    else:
        await ws.send_bytes(make_sync_step2(_EMPTY_UPDATE))


async def remove_client(ws: WebSocket, room: Room) -> None:
    """Remove a client from a room.

    When the room becomes empty, doc_state is reset to empty so the next
    joiner always re-seeds from the database (via the frontend onInitialSync
    path). This prevents stale in-memory Yjs state from diverging from the
    Postgres database, which is the single source of truth for page content.

    Multi-user collaboration is unaffected: doc_state is only cleared when
    ALL clients have left, so a second user joining an active room still
    receives the live Yjs state from the first user.
    """
    room.clients.discard(ws)
    if not room.clients:
        room.doc_state = b""


async def broadcast(data: bytes, sender: WebSocket, room: Room) -> None:
    """Send a message to every client in the room except the sender."""
    dead: set[WebSocket] = set()
    for client in room.clients:
        if client is sender:
            continue
        try:
            await client.send_bytes(data)
        except Exception:
            dead.add(client)
    room.clients -= dead
