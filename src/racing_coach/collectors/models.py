"""Unified telemetry data model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TelemetryFrame:
    """Single frame of telemetry data at a point in time."""

    timestamp_ms: float = 0.0

    # Driver inputs
    throttle: float = 0.0       # 0.0–1.0
    brake: float = 0.0          # 0.0–1.0
    steering: float = 0.0       # -1.0 to 1.0 (left to right)
    gear: int = 0

    # Vehicle dynamics
    speed_kmh: float = 0.0
    rpm: float = 0.0

    # Track position
    normalized_pos: float = 0.0  # 0.0–1.0 along track centerline
    world_x: float = 0.0
    world_y: float = 0.0
    world_z: float = 0.0

    # G-forces
    g_lateral: float = 0.0
    g_longitudinal: float = 0.0

    # Tires (FL, FR, RL, RR)
    tire_temp_core: list[float] = field(default_factory=lambda: [0.0] * 4)
    tire_pressure: list[float] = field(default_factory=lambda: [0.0] * 4)
    wheel_slip: list[float] = field(default_factory=lambda: [0.0] * 4)

    # Session
    fuel: float = 0.0
    current_lap: int = 0
    lap_time_ms: int = 0
    is_in_pit: bool = False

    def to_dict(self) -> dict:
        """Convert to flat dictionary for DataFrame construction."""
        d = {
            "timestamp_ms": self.timestamp_ms,
            "throttle": self.throttle,
            "brake": self.brake,
            "steering": self.steering,
            "gear": self.gear,
            "speed_kmh": self.speed_kmh,
            "rpm": self.rpm,
            "normalized_pos": self.normalized_pos,
            "world_x": self.world_x,
            "world_y": self.world_y,
            "world_z": self.world_z,
            "g_lateral": self.g_lateral,
            "g_longitudinal": self.g_longitudinal,
            "fuel": self.fuel,
            "current_lap": self.current_lap,
            "lap_time_ms": self.lap_time_ms,
            "is_in_pit": self.is_in_pit,
        }
        for i, suffix in enumerate(["fl", "fr", "rl", "rr"]):
            d[f"tire_temp_{suffix}"] = self.tire_temp_core[i]
            d[f"tire_pressure_{suffix}"] = self.tire_pressure[i]
            d[f"wheel_slip_{suffix}"] = self.wheel_slip[i]
        return d
