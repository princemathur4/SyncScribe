# SyncScribe

A real-time collaborative markdown editor for small teams. Multiple users can edit the same page simultaneously, with changes syncing instantly via Yjs CRDTs.

---

## Quick Start

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/) with Compose

```bash
docker-compose up --build
```

App runs at `http://localhost:3000`.

The database is seeded automatically with sample pages and two demo accounts:

| Username | Password    |
|----------|-------------|
| alice    | password123 |
| bob      | password123 |

---

## Features

- **Real-time collaboration** — multiple users edit the same page simultaneously using Yjs CRDTs. Cursor positions and presence are visible live.
- **Markdown editor** — CodeMirror 6 with syntax highlighting and a toggle-able live preview.
- **Nested page tree** — pages can be organized hierarchically; the sidebar shows a collapsible tree with expand/collapse per node.
- **Create pages** — create new pages from the sidebar with an optional parent page, generating a URL slug automatically.
- **Full-text search** — PostgreSQL `tsvector` search with highlighted snippets, debounced as you type.
- **Wiki-links** — click `[[Page Name]]` links in preview to navigate directly to that page.
- **Last edited by** — each page tracks who last edited it and when.
- **JWT authentication** — register/login flow; all write operations require a valid token.

---

## Manual Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL running locally

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:

```env
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/<dbname>
SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Seed the database, then start the server:

```bash
python modules/seed.py
uvicorn app:app --reload --port 8000
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
        |── REST (auth, pages CRUD, search)  →  FastAPI  →  PostgreSQL
        |
        └── WebSocket (/ws/{slug})           →  FastAPI Yjs relay (in-memory)
```

- **Frontend:** React + Vite. CodeMirror 6 handles editing. Yjs manages shared document state across all connected clients. `y-websocket` handles the sync protocol.
- **Backend:** FastAPI. REST routes handle auth and page persistence. A separate WebSocket route acts as a Yjs relay, broadcasting binary updates to all clients in the same room.
- **Database:** PostgreSQL via SQLAlchemy. Stores users, pages (with nested parent/child relationships), and `tsvector` columns for full-text search.

---

## API Overview

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | — | Register a new user |
| POST | `/api/auth/login` | — | Login, returns JWT |
| GET | `/api/auth/me` | ✓ | Current user info |
| GET | `/api/pages/tree` | — | Full page tree (nested) |
| GET | `/api/pages/search?q=` | — | Full-text search with snippets |
| GET | `/api/pages` | — | Flat list of all pages |
| GET | `/api/pages/{slug}` | — | Get a single page |
| POST | `/api/pages` | ✓ | Create a page |
| PUT | `/api/pages/{slug}` | ✓ | Update a page |
| DELETE | `/api/pages/{slug}` | ✓ | Delete a page |
| WS | `/ws/{slug}` | — | Yjs real-time sync room |

---

## Real-Time Sync Strategy

Uses **Yjs**, a CRDT (Conflict-free Replicated Data Type) library.

Every client holds a local copy of the Yjs document. When a user types, Yjs produces a compact binary update. That update is sent over WebSocket to the FastAPI relay, which broadcasts it to all other clients in the same room. Each client applies the update locally. Because CRDTs are mathematically guaranteed to converge, all clients end up with the same document regardless of the order updates arrive.

**Why Yjs over OT (Operational Transform):**
- Yjs requires no server-side understanding of the document. The relay is stateless with respect to document semantics.
- OT requires a central server to transform and sequence every operation.
- Yjs handles offline edits and reconnection automatically via its sync protocol.

**Tradeoff accepted:** The server does not persist the live Yjs state — only the debounced REST saves (every ~2 seconds) hit the database. If the server restarts mid-session, clients resync from the last database snapshot, meaning up to 2 seconds of in-flight edits could be lost.

---

## Known Limitations

- No version history or page diffs.
- No file or image uploads.
- No page-level permissions — all authenticated users can edit all pages.
- Server restart drops in-memory Yjs state; clients recover from the last database save.
