"""Driving performance scoring system."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class DrivingScore:
    """Overall and per-category driving scores (0-100)."""
    overall: float
    braking: float
    throttle: float
    consistency: float
    smoothness: float
    details: dict


def score_lap(df: pd.DataFrame, best_df: pd.DataFrame | None = None) -> DrivingScore:
    """Score a lap's driving quality.

    Args:
        df: Telemetry for the lap to score.
        best_df: Optional best lap for relative comparison.
    """
    # --- Braking score ---
    # Penalize late/hard braking (high brake jerk) and lock-ups
    brake_vals = df["brake"].values
    brake_diff = np.diff(brake_vals, prepend=0)
    brake_jerk = np.std(brake_diff)
    # Lower jerk = smoother braking = higher score
    braking_score = max(0, 100 - brake_jerk * 500)

    # Check for lock-ups (wheel slip spikes)
    slip_cols = [c for c in df.columns if c.startswith("wheel_slip_")]
    if slip_cols:
        max_slip = df[slip_cols].max().max()
        if max_slip > 0.5:
            braking_score *= 0.8  # penalty for lock-ups

    # --- Throttle score ---
    throttle_vals = df["throttle"].values
    throttle_diff = np.diff(throttle_vals, prepend=0)
    throttle_jerk = np.std(throttle_diff)
    throttle_score = max(0, 100 - throttle_jerk * 500)

    # Penalize wheelspin on exit
    if slip_cols:
        throttle_zones = df["throttle"] > 0.5
        if throttle_zones.any():
            exit_slip = df.loc[throttle_zones, slip_cols].max().max()
            if exit_slip > 0.3:
                throttle_score *= 0.85

    # --- Consistency score ---
    if best_df is not None and len(best_df) > 10:
        # Compare speed profiles
        n = min(len(df), len(best_df))
        speed_diff = np.abs(df["speed_kmh"].values[:n] - best_df["speed_kmh"].values[:n])
        avg_diff = np.mean(speed_diff)
        consistency_score = max(0, 100 - avg_diff * 2)
    else:
        # Self-consistency: how stable is speed in straights?
        high_speed = df[df["speed_kmh"] > df["speed_kmh"].quantile(0.75)]
        if len(high_speed) > 5:
            speed_var = high_speed["speed_kmh"].std()
            consistency_score = max(0, 100 - speed_var * 3)
        else:
            consistency_score = 70.0

    # --- Smoothness score ---
    steering_vals = df["steering"].values
    steering_diff = np.diff(steering_vals, prepend=0)
    steering_jerk = np.std(steering_diff)
    smoothness_score = max(0, 100 - steering_jerk * 300)

    # Overall weighted score
    overall = (
        braking_score * 0.3
        + throttle_score * 0.3
        + consistency_score * 0.2
        + smoothness_score * 0.2
    )

    return DrivingScore(
        overall=round(overall, 1),
        braking=round(braking_score, 1),
        throttle=round(throttle_score, 1),
        consistency=round(consistency_score, 1),
        smoothness=round(smoothness_score, 1),
        details={
            "brake_jerk": round(brake_jerk, 4),
            "throttle_jerk": round(throttle_jerk, 4),
            "steering_jerk": round(steering_jerk, 4),
        },
    )
