"""Detect corners from telemetry data using speed and G-force profiles."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.signal import find_peaks


@dataclass
class Corner:
    """A detected corner on the track."""
    id: int
    name: str
    entry_pos: float        # normalized track position (0-1)
    apex_pos: float
    exit_pos: float
    entry_speed: float      # km/h
    min_speed: float        # apex speed
    exit_speed: float
    max_g_lateral: float
    max_braking_g: float


def detect_corners(
    df: pd.DataFrame,
    speed_threshold_pct: float = 0.85,
    min_corner_distance: int = 50,
    smoothing_window: int = 5,
) -> list[Corner]:
    """Detect corners from a single lap's telemetry.

    Identifies corners as local minima in the speed trace, filtered by
    a threshold relative to max speed.

    Args:
        df: Single lap telemetry DataFrame.
        speed_threshold_pct: Speed dips below this fraction of max are corners.
        min_corner_distance: Minimum samples between corner apexes.
        smoothing_window: Rolling window for speed smoothing.
    """
    if df.empty or len(df) < min_corner_distance:
        return []

    speed = df["speed_kmh"].rolling(smoothing_window, center=True, min_periods=1).mean()
    max_speed = speed.max()
    threshold = max_speed * speed_threshold_pct

    # Find local minima in speed (= corner apexes)
    inverted = -speed.values
    peaks, properties = find_peaks(
        inverted,
        distance=min_corner_distance,
        height=-threshold,  # inverted: height > -threshold means speed < threshold
    )

    corners: list[Corner] = []
    pos = df["normalized_pos"].values
    g_lat = df["g_lateral"].values if "g_lateral" in df.columns else np.zeros(len(df))
    g_lon = df["g_longitudinal"].values if "g_longitudinal" in df.columns else np.zeros(len(df))

    for i, apex_idx in enumerate(peaks):
        # Find entry: walk backward from apex to where speed starts dropping
        entry_idx = apex_idx
        for j in range(apex_idx - 1, max(0, apex_idx - min_corner_distance * 2), -1):
            if speed.iloc[j] >= speed.iloc[j + 1]:
                entry_idx = j
            else:
                break

        # Find exit: walk forward from apex to where speed recovers
        exit_idx = apex_idx
        for j in range(apex_idx + 1, min(len(speed), apex_idx + min_corner_distance * 2)):
            if speed.iloc[j] >= speed.iloc[j - 1]:
                exit_idx = j
            else:
                break

        # Extract corner metrics
        corner_slice = slice(entry_idx, exit_idx + 1)
        corners.append(Corner(
            id=i + 1,
            name=f"T{i + 1}",
            entry_pos=float(pos[entry_idx]),
            apex_pos=float(pos[apex_idx]),
            exit_pos=float(pos[exit_idx]),
            entry_speed=float(speed.iloc[entry_idx]),
            min_speed=float(speed.iloc[apex_idx]),
            exit_speed=float(speed.iloc[exit_idx]),
            max_g_lateral=float(np.max(np.abs(g_lat[corner_slice]))),
            max_braking_g=float(np.min(g_lon[corner_slice])),  # most negative = hardest braking
        ))

    return corners
