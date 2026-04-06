from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, pages, websocket


def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api")
    app.include_router(pages.router, prefix="/api")
    app.include_router(websocket.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app
