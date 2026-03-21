"""AI coaching API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..deps import get_coach
from ...coach.coach import Coach

router = APIRouter()


@router.get("/{session_id}/lap/{lap_number}")
def get_coaching(
    session_id: str,
    lap_number: int,
    coach: Coach = Depends(get_coach),
):
    """Get AI coaching advice for a specific lap."""
    try:
        advice = coach.get_coaching(session_id, lap_number)
        return {"advice": advice}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Coach error: {e}")
