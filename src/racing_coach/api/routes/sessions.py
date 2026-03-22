"""Session management API routes."""

from __future__ import annotations

import tempfile
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from ..deps import get_session_store, get_telemetry_store
from ...storage.session_store import SessionStore
from ...storage.telemetry_store import TelemetryStore

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


@router.post("/import")
def import_ld(
    file: UploadFile,
    session_store: SessionStore = Depends(get_session_store),
    telemetry_store: TelemetryStore = Depends(get_telemetry_store),
):
    """Import a MoTeC .ld telemetry file."""
    from ...importer import import_ld_file

    with tempfile.NamedTemporaryFile(suffix=".ld", delete=False) as tmp:
        tmp.write(file.file.read())
        tmp_path = Path(tmp.name)

    try:
        session_id = import_ld_file(tmp_path, session_store, telemetry_store)
    finally:
        tmp_path.unlink(missing_ok=True)

    session = session_store.get_session(session_id)
    laps = session_store.get_laps(session_id)
    return {
        "session_id": session_id,
        "track": session.track,
        "car": session.car,
        "num_laps": len(laps),
    }
