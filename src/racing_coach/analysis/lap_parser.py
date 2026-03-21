"""Detect lap boundaries and sector splits from telemetry data."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class LapBoundary:
    lap_number: int
    start_idx: int
    end_idx: int
    start_time_ms: float
    end_time_ms: float
    lap_time_ms: float


def detect_laps(df: pd.DataFrame) -> list[LapBoundary]:
    """Detect lap boundaries from telemetry DataFrame.

    Uses the `current_lap` column to identify lap transitions.
    """
    if df.empty or "current_lap" not in df.columns:
        return []

    laps: list[LapBoundary] = []
    lap_groups = df.groupby("current_lap")

    for lap_num, group in lap_groups:
        if len(group) < 10:  # skip fragments
            continue
        start_idx = group.index[0]
        end_idx = group.index[-1]
        start_time = group["timestamp_ms"].iloc[0]
        end_time = group["timestamp_ms"].iloc[-1]

        laps.append(LapBoundary(
            lap_number=int(lap_num),
            start_idx=int(start_idx),
            end_idx=int(end_idx),
            start_time_ms=start_time,
            end_time_ms=end_time,
            lap_time_ms=end_time - start_time,
        ))

    return sorted(laps, key=lambda l: l.lap_number)


def split_sectors(
    df: pd.DataFrame,
    sector_boundaries: list[float] | None = None,
) -> list[pd.DataFrame]:
    """Split a single lap's telemetry into sectors.

    Args:
        df: Telemetry for a single lap.
        sector_boundaries: normalized_pos values where sectors split (e.g. [0.33, 0.66]).
                          Defaults to thirds.
    """
    if df.empty:
        return []

    if sector_boundaries is None:
        sector_boundaries = [1 / 3, 2 / 3]

    boundaries = [0.0] + sector_boundaries + [1.0]
    sectors = []

    for i in range(len(boundaries) - 1):
        mask = (df["normalized_pos"] >= boundaries[i]) & (df["normalized_pos"] < boundaries[i + 1])
        sector_df = df[mask].reset_index(drop=True)
        if not sector_df.empty:
            sectors.append(sector_df)

    return sectors
