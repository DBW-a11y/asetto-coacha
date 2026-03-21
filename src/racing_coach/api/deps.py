"""FastAPI dependency helpers."""

from __future__ import annotations

from fastapi import Request

from ..coach.coach import Coach
from ..storage.session_store import SessionStore
from ..storage.telemetry_store import TelemetryStore


def get_session_store(request: Request) -> SessionStore:
    return request.app.state.session_store


def get_telemetry_store(request: Request) -> TelemetryStore:
    return request.app.state.telemetry_store


def get_coach(request: Request) -> Coach:
    return request.app.state.coach
