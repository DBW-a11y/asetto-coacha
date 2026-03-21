"""Compute per-lap and per-corner performance metrics."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .corner_detector import Corner


@dataclass
class LapMetrics:
    """Summary metrics for a single lap."""
    lap_number: int
    lap_time_ms: float
    max_speed: float
    avg_speed: float
    avg_throttle: float
    avg_brake: float
    brake_count: int
    max_g_lateral: float
    max_g_longitudinal: float
    throttle_smoothness: float  # std of throttle derivative
    brake_smoothness: float
    fuel_used: float
    avg_tire_temp: float


@dataclass
class CornerMetrics:
    """Detailed metrics for a single corner in a lap."""
    corner_id: int
    corner_name: str
    entry_speed: float
    min_speed: float
    exit_speed: float
    brake_point_pos: float       # where braking starts
    throttle_on_pos: float       # where throttle is reapplied
    time_in_corner_ms: float
    max_g_lateral: float
    max_braking_g: float
    trail_braking_pct: float     # % of corner with brake > 0


def compute_lap_metrics(df: pd.DataFrame, lap_number: int) -> LapMetrics:
    """Compute summary metrics for a single lap."""
    dt = np.diff(df["timestamp_ms"].values, prepend=df["timestamp_ms"].iloc[0])
    dt[0] = dt[1] if len(dt) > 1 else 10  # fix first sample

    # Throttle smoothness = std of throttle rate of change
    throttle_diff = np.diff(df["throttle"].values, prepend=df["throttle"].iloc[0])
    brake_diff = np.diff(df["brake"].values, prepend=df["brake"].iloc[0])

    # Count distinct braking events
    brake_active = (df["brake"] > 0.05).astype(int)
    brake_starts = np.diff(brake_active.values, prepend=0)
    brake_count = int(np.sum(brake_starts > 0))

    tire_temps = []
    for suffix in ["fl", "fr", "rl", "rr"]:
        col = f"tire_temp_{suffix}"
        if col in df.columns:
            tire_temps.append(df[col].mean())

    return LapMetrics(
        lap_number=lap_number,
        lap_time_ms=df["timestamp_ms"].iloc[-1] - df["timestamp_ms"].iloc[0],
        max_speed=float(df["speed_kmh"].max()),
        avg_speed=float(df["speed_kmh"].mean()),
        avg_throttle=float(df["throttle"].mean()),
        avg_brake=float(df["brake"].mean()),
        brake_count=brake_count,
        max_g_lateral=float(df["g_lateral"].abs().max()) if "g_lateral" in df else 0.0,
        max_g_longitudinal=float(df["g_longitudinal"].abs().max()) if "g_longitudinal" in df else 0.0,
        throttle_smoothness=float(np.std(throttle_diff)),
        brake_smoothness=float(np.std(brake_diff)),
        fuel_used=float(df["fuel"].iloc[0] - df["fuel"].iloc[-1]) if "fuel" in df else 0.0,
        avg_tire_temp=float(np.mean(tire_temps)) if tire_temps else 0.0,
    )


def compute_corner_metrics(
    df: pd.DataFrame,
    corner: Corner,
) -> CornerMetrics:
    """Compute detailed metrics for a single corner."""
    # Select frames within the corner boundaries
    mask = (df["normalized_pos"] >= corner.entry_pos) & (df["normalized_pos"] <= corner.exit_pos)
    cdf = df[mask]

    if cdf.empty:
        return CornerMetrics(
            corner_id=corner.id, corner_name=corner.name,
            entry_speed=0, min_speed=0, exit_speed=0,
            brake_point_pos=0, throttle_on_pos=0, time_in_corner_ms=0,
            max_g_lateral=0, max_braking_g=0, trail_braking_pct=0,
        )

    # Find brake point: first frame with brake > 0.1
    braking_frames = cdf[cdf["brake"] > 0.1]
    brake_point_pos = float(braking_frames["normalized_pos"].iloc[0]) if len(braking_frames) > 0 else corner.entry_pos

    # Find throttle application point: after apex, first frame with throttle > 0.1
    apex_mask = cdf["speed_kmh"] == cdf["speed_kmh"].min()
    apex_idx = cdf[apex_mask].index[0] if apex_mask.any() else cdf.index[len(cdf) // 2]
    post_apex = cdf.loc[apex_idx:]
    throttle_frames = post_apex[post_apex["throttle"] > 0.1]
    throttle_on_pos = float(throttle_frames["normalized_pos"].iloc[0]) if len(throttle_frames) > 0 else corner.exit_pos

    # Trail braking: percentage of corner where brake > 0
    trail_braking_pct = float((cdf["brake"] > 0.05).mean()) * 100

    time_ms = cdf["timestamp_ms"].iloc[-1] - cdf["timestamp_ms"].iloc[0]

    return CornerMetrics(
        corner_id=corner.id,
        corner_name=corner.name,
        entry_speed=float(cdf["speed_kmh"].iloc[0]),
        min_speed=float(cdf["speed_kmh"].min()),
        exit_speed=float(cdf["speed_kmh"].iloc[-1]),
        brake_point_pos=brake_point_pos,
        throttle_on_pos=throttle_on_pos,
        time_in_corner_ms=float(time_ms),
        max_g_lateral=float(cdf["g_lateral"].abs().max()) if "g_lateral" in cdf else 0.0,
        max_braking_g=float(cdf["g_longitudinal"].min()) if "g_longitudinal" in cdf else 0.0,
        trail_braking_pct=trail_braking_pct,
    )
