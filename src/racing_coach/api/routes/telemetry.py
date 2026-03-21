"""Telemetry data API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import get_telemetry_store
from ...storage.telemetry_store import TelemetryStore

router = APIRouter()


@router.get("/{session_id}")
def get_session_telemetry(
    session_id: str,
    store: TelemetryStore = Depends(get_telemetry_store),
    downsample: int = Query(1, ge=1, description="Keep every Nth row"),
):
    """Get telemetry data for a session."""
    df = store.read_session(session_id)
    if df.empty:
        raise HTTPException(status_code=404, detail="No telemetry data found")
    if downsample > 1:
        df = df.iloc[::downsample]
    return df.to_dict(orient="list")


@router.get("/{session_id}/lap/{lap_number}")
def get_lap_telemetry(
    session_id: str,
    lap_number: int,
    store: TelemetryStore = Depends(get_telemetry_store),
    downsample: int = Query(1, ge=1),
):
    """Get telemetry data for a specific lap."""
    df = store.read_lap(session_id, lap_number)
    if df.empty:
        raise HTTPException(status_code=404, detail="No telemetry data for this lap")
    if downsample > 1:
        df = df.iloc[::downsample]
    return df.to_dict(orient="list")
