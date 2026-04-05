# LiveDraft

A real-time collaborative markdown editor for small teams.

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:3000`.

---

## Architecture

```
Browser (React + CodeMirror 6 + Yjs)
        |
        | WebSocket (/ws/{room})
        |
FastAPI WebSocket Relay
        |
In memory (page persistence)
Postgres DB to be added 
```

- **Frontend:** React + Vite. CodeMirror 6 handles the editor. Yjs manages the shared document state across all connected clients.
- **Backend:** FastAPI with async WebSocket routes. Acts as a relay, broadcasting Yjs binary updates to all clients in the same room. Does not parse Yjs messages.

---

## Real-Time Sync Strategy

Uses **Yjs**, a CRDT (Conflict-free Replicated Data Type) library.

Every client holds a local copy of the Yjs document. When a user types, Yjs generates a compact binary update. That update is sent over WebSocket to the FastAPI relay, which broadcasts it to all other clients in the room. Each client applies the update to their local copy. Because CRDTs are mathematically guaranteed to converge, all clients always end up with the same document regardless of the order updates arrive.

**Why Yjs over OT (Operational Transform):**
- Yjs requires no server-side understanding of the document. The relay is stateless.
- OT requires a central server to transform and sequence every operation, adding complexity and a stateful server requirement.
- Yjs handles offline edits and reconnection automatically via its sync protocol.
**Tradeoff accepted:** The server does not hold the authoritative Yjs document state in memory. 
If the server restarts while users are editing, clients resync from the last saved database snapshot, meaning up to 2 seconds of unsaved edits could be lost.

---

## Known Limitations

- No version history or page diffs.
- No file or image uploads.
- No page-level permissions (all authenticated users can edit all pages).
- Server restart drops in-memory Yjs state. Clients to recover from last database save.

---

