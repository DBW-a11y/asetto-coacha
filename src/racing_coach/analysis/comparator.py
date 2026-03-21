"""Compare two laps: align by track position and compute deltas."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d


@dataclass
class LapComparison:
    """Result of comparing two laps."""
    positions: np.ndarray           # normalized positions (0-1)
    delta_time_ms: np.ndarray       # cumulative time delta (positive = ref is faster)
    delta_speed: np.ndarray         # speed difference (target - ref)
    ref_speed: np.ndarray
    target_speed: np.ndarray
    ref_throttle: np.ndarray
    target_throttle: np.ndarray
    ref_brake: np.ndarray
    target_brake: np.ndarray
    total_delta_ms: float           # total time difference

    def to_dict(self) -> dict:
        return {
            "positions": self.positions.tolist(),
            "delta_time_ms": self.delta_time_ms.tolist(),
            "delta_speed": self.delta_speed.tolist(),
            "ref_speed": self.ref_speed.tolist(),
            "target_speed": self.target_speed.tolist(),
            "ref_throttle": self.ref_throttle.tolist(),
            "target_throttle": self.target_throttle.tolist(),
            "ref_brake": self.ref_brake.tolist(),
            "target_brake": self.target_brake.tolist(),
            "total_delta_ms": self.total_delta_ms,
        }


def _resample_by_position(df: pd.DataFrame, positions: np.ndarray) -> dict[str, np.ndarray]:
    """Resample telemetry to uniform track positions using interpolation."""
    pos = df["normalized_pos"].values
    # Handle wrap-around (pos goes from ~1 back to ~0)
    # Ensure monotonically increasing by unwrapping
    dpos = np.diff(pos)
    wrap_indices = np.where(dpos < -0.5)[0]
    for idx in wrap_indices:
        pos[idx + 1:] += 1.0

    # Remove duplicate positions for interpolation
    _, unique_idx = np.unique(pos, return_index=True)
    pos = pos[unique_idx]

    result = {}
    for col in ["speed_kmh", "throttle", "brake", "timestamp_ms", "g_lateral", "g_longitudinal"]:
        if col in df.columns:
            values = df[col].values[unique_idx]
            try:
                f = interp1d(pos, values, kind="linear", fill_value="extrapolate")
                result[col] = f(positions)
            except ValueError:
                result[col] = np.zeros_like(positions)
    return result


def compare_laps(ref_df: pd.DataFrame, target_df: pd.DataFrame, num_points: int = 500) -> LapComparison:
    """Compare target lap against reference lap.

    Both DataFrames should contain a single lap's telemetry.
    Returns delta metrics sampled at uniform track positions.

    Args:
        ref_df: Reference (faster) lap telemetry.
        target_df: Target (comparison) lap telemetry.
        num_points: Number of sample points along the track.
    """
    positions = np.linspace(0.001, 0.999, num_points)

    ref = _resample_by_position(ref_df, positions)
    target = _resample_by_position(target_df, positions)

    # Compute cumulative time delta
    ref_time = ref["timestamp_ms"] - ref["timestamp_ms"][0]
    target_time = target["timestamp_ms"] - target["timestamp_ms"][0]
    delta_time = target_time - ref_time  # positive = target is slower

    return LapComparison(
        positions=positions,
        delta_time_ms=delta_time,
        delta_speed=target["speed_kmh"] - ref["speed_kmh"],
        ref_speed=ref["speed_kmh"],
        target_speed=target["speed_kmh"],
        ref_throttle=ref.get("throttle", np.zeros_like(positions)),
        target_throttle=target.get("throttle", np.zeros_like(positions)),
        ref_brake=ref.get("brake", np.zeros_like(positions)),
        target_brake=target.get("brake", np.zeros_like(positions)),
        total_delta_ms=float(delta_time[-1]),
    )
