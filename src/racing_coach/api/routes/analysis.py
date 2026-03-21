"""Analysis API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_coach, get_telemetry_store
from ...coach.coach import Coach
from ...storage.telemetry_store import TelemetryStore
from ...analysis.comparator import compare_laps

router = APIRouter()


@router.get("/{session_id}/lap/{lap_number}")
def analyze_lap(
    session_id: str,
    lap_number: int,
    coach: Coach = Depends(get_coach),
):
    """Get full analysis for a specific lap."""
    try:
        return coach.analyze_lap(session_id, lap_number)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{session_id}/compare")
def compare(
    session_id: str,
    ref_lap: int,
    target_lap: int,
    store: TelemetryStore = Depends(get_telemetry_store),
):
    """Compare two laps from the same session."""
    ref_df = store.read_lap(session_id, ref_lap)
    target_df = store.read_lap(session_id, target_lap)

    if ref_df.empty:
        raise HTTPException(status_code=404, detail=f"No data for lap {ref_lap}")
    if target_df.empty:
        raise HTTPException(status_code=404, detail=f"No data for lap {target_lap}")

    comparison = compare_laps(ref_df, target_df)
    return comparison.to_dict()
