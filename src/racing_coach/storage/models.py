"""Database models for session and lap metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Session:
    id: str
    track: str
    car: str
    started_at: datetime
    ended_at: datetime | None = None
    num_laps: int = 0
    best_lap_time_ms: int | None = None


@dataclass
class Lap:
    id: int
    session_id: str
    lap_number: int
    lap_time_ms: int
    is_valid: bool = True
    sector1_ms: int | None = None
    sector2_ms: int | None = None
    sector3_ms: int | None = None
