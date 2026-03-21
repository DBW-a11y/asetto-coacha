"""Live telemetry WebSocket route."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)

# Connected WebSocket clients for live telemetry broadcast
_clients: set[WebSocket] = set()


@router.websocket("/ws")
async def telemetry_ws(websocket: WebSocket):
    """WebSocket endpoint for real-time telemetry streaming."""
    await websocket.accept()
    _clients.add(websocket)
    logger.info("WebSocket client connected (total: %d)", len(_clients))

    try:
        while True:
            # Keep connection alive; client sends pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        _clients.discard(websocket)
        logger.info("WebSocket client disconnected (total: %d)", len(_clients))


async def broadcast_frame(frame_dict: dict) -> None:
    """Broadcast a telemetry frame to all connected WebSocket clients."""
    if not _clients:
        return

    message = json.dumps(frame_dict)
    dead: list[WebSocket] = []

    for ws in _clients:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)

    for ws in dead:
        _clients.discard(ws)
