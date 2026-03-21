"""Coach orchestrator: analysis → prompt → LLM → advice."""

from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd


def _to_json_safe(obj):
    """Recursively convert numpy types to Python natives for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _to_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_safe(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.bool_):
        return bool(obj)
    from datetime import datetime
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

from ..analysis.comparator import LapComparison, compare_laps
from ..analysis.corner_detector import Corner, detect_corners
from ..analysis.metrics import (
    CornerMetrics,
    LapMetrics,
    compute_corner_metrics,
    compute_lap_metrics,
)
from ..analysis.scoring import DrivingScore, score_lap
from ..storage.session_store import SessionStore
from ..storage.telemetry_store import TelemetryStore
from .llm_client import LLMClient
from .prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class Coach:
    """Orchestrates the full analysis and coaching pipeline."""

    def __init__(
        self,
        session_store: SessionStore,
        telemetry_store: TelemetryStore,
        llm_client: LLMClient,
        prompt_builder: PromptBuilder | None = None,
    ):
        self._session_store = session_store
        self._telemetry_store = telemetry_store
        self._llm = llm_client
        self._prompt_builder = prompt_builder or PromptBuilder()

    def analyze_lap(
        self,
        session_id: str,
        lap_number: int,
    ) -> dict:
        """Run full analysis on a single lap. Returns structured results."""
        session = self._session_store.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        df = self._telemetry_store.read_lap(session_id, lap_number)
        if df.empty:
            raise ValueError(f"No telemetry for lap {lap_number} in session {session_id}")

        # Compute metrics
        metrics = compute_lap_metrics(df, lap_number)

        # Detect corners and compute corner metrics
        corners = detect_corners(df)
        corner_metrics = [compute_corner_metrics(df, c) for c in corners]

        # Score the lap
        best_lap_df = self._get_best_lap_df(session_id)
        score = score_lap(df, best_lap_df)

        # Compare with best lap
        comparison = None
        if best_lap_df is not None and session.best_lap_time_ms:
            best_laps = self._session_store.get_laps(session_id)
            best_lap = min((l for l in best_laps if l.is_valid), key=lambda l: l.lap_time_ms, default=None)
            if best_lap and best_lap.lap_number != lap_number:
                comparison = compare_laps(best_lap_df, df)

        return _to_json_safe({
            "session": asdict(session),
            "lap_number": lap_number,
            "metrics": asdict(metrics),
            "corners": [asdict(cm) for cm in corner_metrics],
            "score": asdict(score),
            "comparison": comparison.to_dict() if comparison else None,
        })

    def get_coaching(
        self,
        session_id: str,
        lap_number: int,
    ) -> str:
        """Get AI coaching advice for a specific lap."""
        session = self._session_store.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        analysis = self.analyze_lap(session_id, lap_number)

        # Reconstruct typed objects for prompt builder
        metrics = LapMetrics(**analysis["metrics"])
        score = DrivingScore(**analysis["score"])
        corner_metrics = [CornerMetrics(**c) for c in analysis["corners"]]
        comparison = None
        if analysis["comparison"]:
            import numpy as np
            comp = analysis["comparison"]
            comparison = LapComparison(**{
                k: np.array(v) if isinstance(v, list) else v
                for k, v in comp.items()
            })

        prompt = self._prompt_builder.build_lap_analysis_prompt(
            track=session.track,
            car=session.car,
            lap_number=lap_number,
            lap_time_ms=metrics.lap_time_ms,
            metrics=metrics,
            score=score,
            corners=corner_metrics,
            comparison=comparison,
            best_lap_time_ms=session.best_lap_time_ms,
        )

        system = self._prompt_builder.system_prompt()
        return self._llm.chat(system=system, user=prompt)

    def _get_best_lap_df(self, session_id: str) -> pd.DataFrame | None:
        laps = self._session_store.get_laps(session_id)
        valid_laps = [l for l in laps if l.is_valid]
        if not valid_laps:
            return None
        best = min(valid_laps, key=lambda l: l.lap_time_ms)
        df = self._telemetry_store.read_lap(session_id, best.lap_number)
        return df if not df.empty else None
