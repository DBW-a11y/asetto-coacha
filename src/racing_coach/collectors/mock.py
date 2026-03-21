"""Mock telemetry collector for development and testing.

Generates realistic-looking telemetry data simulating laps around a circuit,
or replays previously recorded Parquet files.
"""

from __future__ import annotations

import asyncio
import math
import time
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from .base import TelemetryCollector
from .models import TelemetryFrame

logger = logging.getLogger(__name__)


class MockCollector(TelemetryCollector):
    """Generates synthetic telemetry data or replays from a Parquet file."""

    def __init__(
        self,
        sample_rate_hz: int = 100,
        replay_file: Path | None = None,
        num_laps: int = 5,
        lap_length_m: float = 4300.0,
    ):
        self._sample_rate_hz = sample_rate_hz
        self._interval = 1.0 / sample_rate_hz
        self._connected = False
        self._replay_file = replay_file
        self._num_laps = num_laps
        self._lap_length_m = lap_length_m

        # State for synthetic generation
        self._frame_idx = 0
        self._start_time: float = 0
        self._current_lap = 0

        # Replay state
        self._replay_df: pd.DataFrame | None = None
        self._replay_idx = 0

    async def connect(self) -> None:
        if self._replay_file and self._replay_file.exists():
            self._replay_df = pd.read_parquet(self._replay_file)
            logger.info("Mock collector: replaying %d frames from %s",
                        len(self._replay_df), self._replay_file)
        else:
            logger.info("Mock collector: generating synthetic telemetry (%d laps)", self._num_laps)
        self._start_time = time.time()
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False
        self._replay_df = None
        logger.info("Mock collector disconnected")

    def is_connected(self) -> bool:
        return self._connected

    async def read_frame(self) -> TelemetryFrame | None:
        if not self._connected:
            return None

        await asyncio.sleep(self._interval)

        if self._replay_df is not None:
            return self._read_replay_frame()
        return self._generate_synthetic_frame()

    def _read_replay_frame(self) -> TelemetryFrame | None:
        df = self._replay_df
        if self._replay_idx >= len(df):
            self._connected = False
            return None

        row = df.iloc[self._replay_idx]
        self._replay_idx += 1

        return TelemetryFrame(
            timestamp_ms=row.get("timestamp_ms", time.time() * 1000),
            throttle=row.get("throttle", 0),
            brake=row.get("brake", 0),
            steering=row.get("steering", 0),
            gear=int(row.get("gear", 0)),
            speed_kmh=row.get("speed_kmh", 0),
            rpm=row.get("rpm", 0),
            normalized_pos=row.get("normalized_pos", 0),
            world_x=row.get("world_x", 0),
            world_y=row.get("world_y", 0),
            world_z=row.get("world_z", 0),
            g_lateral=row.get("g_lateral", 0),
            g_longitudinal=row.get("g_longitudinal", 0),
            tire_temp_core=[
                row.get("tire_temp_fl", 80),
                row.get("tire_temp_fr", 80),
                row.get("tire_temp_rl", 80),
                row.get("tire_temp_rr", 80),
            ],
            tire_pressure=[
                row.get("tire_pressure_fl", 26),
                row.get("tire_pressure_fr", 26),
                row.get("tire_pressure_rl", 26),
                row.get("tire_pressure_rr", 26),
            ],
            wheel_slip=[
                row.get("wheel_slip_fl", 0),
                row.get("wheel_slip_fr", 0),
                row.get("wheel_slip_rl", 0),
                row.get("wheel_slip_rr", 0),
            ],
            fuel=row.get("fuel", 50),
            current_lap=int(row.get("current_lap", 0)),
            lap_time_ms=int(row.get("lap_time_ms", 0)),
            is_in_pit=bool(row.get("is_in_pit", False)),
        )

    def _generate_synthetic_frame(self) -> TelemetryFrame | None:
        """Generate a synthetic frame simulating a circuit lap."""
        elapsed = time.time() - self._start_time
        t_ms = elapsed * 1000

        # ~90 seconds per lap
        lap_period = 90.0
        total_time = lap_period * self._num_laps
        if elapsed > total_time:
            self._connected = False
            return None

        current_lap = int(elapsed / lap_period)
        lap_progress = (elapsed % lap_period) / lap_period  # 0..1

        # Simulate a circuit with straights and corners
        # Use sine waves to create speed variation (corners = low speed)
        corner_factor = (
            0.3 * math.sin(2 * math.pi * 6 * lap_progress)
            + 0.2 * math.sin(2 * math.pi * 3 * lap_progress + 1.0)
            + 0.1 * math.sin(2 * math.pi * 10 * lap_progress + 2.5)
        )

        base_speed = 180.0
        speed = base_speed + corner_factor * 80.0
        speed = max(40.0, min(290.0, speed))

        # Derive inputs from speed profile
        speed_derivative = -80.0 * (
            0.3 * 2 * math.pi * 6 * math.cos(2 * math.pi * 6 * lap_progress)
            + 0.2 * 2 * math.pi * 3 * math.cos(2 * math.pi * 3 * lap_progress + 1.0)
        ) / lap_period

        throttle = max(0.0, min(1.0, 0.5 + speed_derivative * 0.005))
        brake = max(0.0, min(1.0, -speed_derivative * 0.005))

        # Steering from lateral position changes
        steering = 0.3 * math.sin(2 * math.pi * 8 * lap_progress)
        steering = max(-1.0, min(1.0, steering))

        # Gear from speed
        gear_thresholds = [0, 60, 100, 140, 180, 220, 260]
        gear = 1
        for i, threshold in enumerate(gear_thresholds):
            if speed > threshold:
                gear = i + 1

        # World coordinates - oval-ish circuit
        angle = 2 * math.pi * lap_progress
        rx, ry = 300.0, 200.0
        world_x = rx * math.cos(angle) + 20 * math.sin(3 * angle)
        world_z = ry * math.sin(angle) + 15 * math.cos(5 * angle)

        # G-forces
        g_lat = steering * speed / 100.0 * 1.5
        g_lon = speed_derivative / 100.0

        # Add slight per-lap variation
        rng = np.random.default_rng(self._frame_idx)
        noise = rng.normal(0, 0.02)

        self._frame_idx += 1

        return TelemetryFrame(
            timestamp_ms=t_ms,
            throttle=max(0.0, min(1.0, throttle + noise)),
            brake=max(0.0, min(1.0, brake + abs(noise))),
            steering=steering,
            gear=gear,
            speed_kmh=speed + rng.normal(0, 1),
            rpm=speed * 35 + 2000 + rng.normal(0, 50),
            normalized_pos=lap_progress,
            world_x=world_x,
            world_y=0.0,
            world_z=world_z,
            g_lateral=g_lat + rng.normal(0, 0.05),
            g_longitudinal=g_lon + rng.normal(0, 0.05),
            tire_temp_core=[80 + rng.normal(0, 2) for _ in range(4)],
            tire_pressure=[26.5 + rng.normal(0, 0.3) for _ in range(4)],
            wheel_slip=[max(0, abs(brake) * 0.1 + rng.normal(0, 0.02)) for _ in range(4)],
            fuel=50.0 - elapsed * 0.05,
            current_lap=current_lap,
            lap_time_ms=int((elapsed % lap_period) * 1000),
            is_in_pit=False,
        )
