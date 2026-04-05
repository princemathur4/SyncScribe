import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# rooms: maps room_name -> list of connected WebSockets
# e.g. { "my-page": [ws1, ws2, ws3] }
rooms: dict[str, list[WebSocket]] = {}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/{room_name}")
async def websocket_endpoint(websocket: WebSocket, room_name: str):
    await websocket.accept()

    # Add this socket to the room
    if room_name not in rooms:
        rooms[room_name] = []
    rooms[room_name].append(websocket)

    print(f"[+] Client joined room '{room_name}'. "
          f"Total in room: {len(rooms[room_name])}")

    try:
        while True:
            # Yjs sends binary messages (Uint8Array updates)
            # Receive as bytes, broadcast to everyone else in the room
            data = await websocket.receive_bytes()
            print("data:", data)
            for other in rooms[room_name]:
                if other is not websocket:
                    await other.send_bytes(data)

    except WebSocketDisconnect:
        rooms[room_name].remove(websocket)
        print(f"[-] Client left room '{room_name}'. "
              f"Remaining: {len(rooms[room_name])}")

        # Clean up empty rooms
        if len(rooms[room_name]) == 0:
            del rooms[room_name]