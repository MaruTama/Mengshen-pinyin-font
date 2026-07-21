# -*- coding: utf-8 -*-
"""FastAPI application for the Mengshen Font Studio webapp.

Run from the repository root:
    uvicorn webapp.backend.main:app --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import settings
from .api import build, duoyinzi, glyphs, meta, preview, projects, readings
from .api.deps import tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_directories()
    tasks.recover_stale_tasks()
    yield
    tasks.executor.shutdown(wait=False, cancel_futures=True)


def create_app() -> FastAPI:
    app = FastAPI(title="Mengshen Font Studio", lifespan=lifespan)

    # Local-only app; allow the Vite dev server origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(meta.router)
    app.include_router(projects.router)
    app.include_router(preview.router)
    app.include_router(glyphs.router)
    app.include_router(duoyinzi.router)
    app.include_router(readings.router)
    app.include_router(build.router)

    if settings.FRONTEND_DIST.exists():
        app.mount(
            "/assets",
            StaticFiles(directory=settings.FRONTEND_DIST / "assets"),
            name="assets",
        )

        # SPA fallback: any non-API path serves the frontend entry point.
        # index.html must never be cached, or the browser keeps loading a
        # stale bundle after a rebuild (asset filenames are content-hashed,
        # so only the HTML that references them needs revalidation).
        @app.get("/{path:path}", include_in_schema=False)
        async def spa_fallback(path: str) -> FileResponse:
            static_file = settings.FRONTEND_DIST / path
            if path and ".." not in path and static_file.is_file():
                return FileResponse(static_file)
            return FileResponse(
                settings.FRONTEND_DIST / "index.html",
                headers={"Cache-Control": "no-cache"},
            )

    return app


app = create_app()
