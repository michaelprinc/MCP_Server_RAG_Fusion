"""FastAPI application entry point for MCP server."""

from __future__ import annotations

import os
import time
from typing import Any, Dict

from fastapi import APIRouter, FastAPI, HTTPException

from .mcp_handlers import build_state, register_routes, ServerState
from .models import AdminReloadResponse

APP_START_TIME = time.time()

app = FastAPI(
    title="RAG-Fusion MCP Server",
    description="Dual-index retrieval fusion with MCP-compatible endpoints.",
    version="0.1.0",
)

mcp_router = APIRouter(prefix="/mcp", tags=["mcp"])
app.state.server_state = None


def get_state() -> ServerState:
    state = app.state.server_state
    if state is None:
        raise HTTPException(status_code=503, detail="Server state not initialized.")
    return state


@app.on_event("startup")
async def startup_event() -> None:
    app.state.server_state = build_state(dict(os.environ))
    register_routes(mcp_router, app.state.server_state)
    app.include_router(mcp_router)


@app.get("/health")
async def health() -> Dict[str, Any]:
    state = get_state()
    uptime_seconds = int(time.time() - APP_START_TIME)
    return {
        "status": "healthy",
        "version": state.index_version,
        "uptime_seconds": uptime_seconds,
    }


@app.post("/admin/reload", response_model=AdminReloadResponse)
async def admin_reload() -> AdminReloadResponse:
    state = get_state()
    state.retriever.reload()
    state.cache.clear()
    return AdminReloadResponse(status="reloaded", index_version=state.index_version)


@app.get("/metrics")
async def metrics() -> Dict[str, Any]:
    state = get_state()
    return {
        "cache_size": state.cache.currsize,
        "cache_max": state.cache.maxsize,
        "index_version": state.index_version,
    }
