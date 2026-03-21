"""Session management API routes."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_session_store
from ...storage.session_store import SessionStore

router = APIRouter()


@router.get("/")
def list_sessions(
    limit: int = 50,
    store: SessionStore = Depends(get_session_store),
):
    """List all recording sessions."""
    sessions = store.list_sessions(limit=limit)
    return [asdict(s) for s in sessions]


@router.get("/{session_id}")
def get_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
):
    """Get a single session with its laps."""
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    laps = store.get_laps(session_id)
    return {
        **asdict(session),
        "laps": [asdict(l) for l in laps],
    }
