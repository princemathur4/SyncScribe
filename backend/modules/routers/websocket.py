from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..realtime.rooms import (
    Room,
    broadcast,
    build_sync_step1,
    extract_update,
    get_or_create_room,
    remove_client,
    send_server_state,
    store_update,
)

router = APIRouter()

# y-websocket binary protocol constants
_MSG_SYNC = 0
_MSG_AWARENESS = 1
_SYNC_STEP1 = 0   # client → server: "here is my state vector, send me what I'm missing"
_SYNC_STEP2 = 1   # server ↔ client: "here are the updates you are missing"
_SYNC_UPDATE = 2  # client → server: incremental update (a live edit)


@router.websocket("/ws/{room_name}")
async def yjs_room(websocket: WebSocket, room_name: str):
    await websocket.accept()

    room: Room = get_or_create_room(room_name)
    room.clients.add(websocket)
    print(f"[+] Client joined '{room_name}'. Total: {len(room.clients)}")

    # Proactive handshake — the server initiates sync as per the y-websocket
    # server protocol (both sides start simultaneously):
    #   1. Sync step 1: "I have nothing, send me your full state."
    #   2. Sync step 2: "Here is what I currently have."
    # Receiving the sync step 2 causes provider.synced = true on the client
    # and fires the 'sync' event, which is what triggers initial content seeding.
    await websocket.send_bytes(build_sync_step1())
    await send_server_state(websocket, room)

    try:
        while True:
            data = await websocket.receive_bytes()

            if len(data) < 2:
                continue

            if data[0] == _MSG_SYNC:
                sync_type = data[1]

                if sync_type == _SYNC_STEP1:
                    # Reactive path: client re-requesting state (e.g. reconnect).
                    await send_server_state(websocket, room)

                elif sync_type in (_SYNC_STEP2, _SYNC_UPDATE):
                    # Client pushing its state or a live edit.
                    # Persist so future joiners can catch up, then relay to peers.
                    update = extract_update(data)
                    if update:
                        store_update(room, update)
                    await broadcast(data, websocket, room)

            elif data[0] == _MSG_AWARENESS:
                # Presence / cursor data — ephemeral, relay only.
                await broadcast(data, websocket, room)

            else:
                # Unknown message type: broadcast as-is for forward compatibility.
                await broadcast(data, websocket, room)

    except WebSocketDisconnect:
        await remove_client(websocket, room)
        print(f"[-] Client left '{room_name}'. Remaining: {len(room.clients)}")

    except Exception as e:
        print(f"[!] Error in room '{room_name}': {e}")
        await remove_client(websocket, room)
