"""Import MoTeC .ld files into the Racing Coach storage pipeline."""

from __future__ import annotations

import logging
from pathlib import Path

from .collectors.models import TelemetryFrame
from .collectors.motec_ld import LdFile
from .storage.session_store import SessionStore
from .storage.telemetry_store import TelemetryStore

logger = logging.getLogger(__name__)

# MoTeC channel name → (TelemetryFrame field, transform)
# transform is applied as: frame_value = transform(decoded_value)
_CHANNEL_MAP: list[tuple[str, str, object]] = [
    ("Ground Speed",           "speed_kmh",     None),
    ("Throttle Pos",           "throttle",      lambda v: v / 100.0),
    ("Brake Pos",              "brake",         lambda v: v / 100.0),
    ("Steering Angle",         "steering",      lambda v: max(-1.0, min(1.0, v / 450.0))),
    ("Gear",                   "gear",          lambda v: round(v)),
    ("Engine RPM",             "rpm",           None),
    ("Car Pos Norm",           "normalized_pos", None),
    ("Car Coord X",            "world_x",       None),
    ("Car Coord Y",            "world_y",       None),
    ("Car Coord Z",            "world_z",       None),
    ("CG Accel Lateral",       "g_lateral",     None),
    ("CG Accel Longitudinal",  "g_longitudinal", None),
    ("Fuel Level",             "fuel",          None),
    ("Session Lap Count",      "current_lap",   lambda v: round(v)),
    ("Lap Time",               "lap_time_ms",   lambda v: int(v * 1000)),
    ("In Pit",                 "is_in_pit",     lambda v: bool(round(v))),
]

# Tire channels:  MoTeC name suffix → (frame list field, index)
_TIRE_SUFFIXES = ["FL", "FR", "RL", "RR"]

_TIRE_CHANNELS: list[tuple[str, str, object]] = [
    ("Tire Temp Core",  "tire_temp_core",  None),
    ("Tire Pressure",   "tire_pressure",   None),
    ("Tire Slip Ratio", "wheel_slip",      lambda v: v / 100.0),
]


def _decode_or_zeros(ld: LdFile, name: str, transform: object = None) -> list[float]:
    """Decode a channel, returning zeros if not present."""
    if not ld.has(name):
        return [0.0] * ld.num_samples
    vals = ld.decode(name)
    if transform is not None:
        vals = [transform(v) for v in vals]
    return vals


def import_ld_file(
    ld_path: str | Path,
    session_store: SessionStore,
    telemetry_store: TelemetryStore,
) -> str:
    """Import a MoTeC .ld file and return the new session_id."""
    ld_path = Path(ld_path)
    logger.info("Importing %s", ld_path.name)

    ld = LdFile.from_file(ld_path)
    track = ld.venue or "unknown"
    car = ld.vehicle or "unknown"
    session_id = session_store.create_session(track, car)

    n = ld.num_samples
    rate = ld.sample_rate
    dt_ms = 1000.0 / rate  # ms per sample

    # Pre-decode all mapped channels
    columns: dict[str, list] = {}
    for motec_name, field, transform in _CHANNEL_MAP:
        columns[field] = _decode_or_zeros(ld, motec_name, transform)

    # Pre-decode tire channels (4 corners each)
    tire_data: dict[str, list[list[float]]] = {}
    for prefix, field, transform in _TIRE_CHANNELS:
        corners = []
        for suffix in _TIRE_SUFFIXES:
            ch_name = f"{prefix} {suffix}"
            corners.append(_decode_or_zeros(ld, ch_name, transform))
        tire_data[field] = corners

    # Build frames and detect lap transitions
    frames: list[dict] = []
    prev_lap = round(columns["current_lap"][0]) if n > 0 else 0

    for i in range(n):
        frame = TelemetryFrame(
            timestamp_ms=i * dt_ms,
            speed_kmh=columns["speed_kmh"][i],
            throttle=columns["throttle"][i],
            brake=columns["brake"][i],
            steering=columns["steering"][i],
            gear=int(columns["gear"][i]),
            rpm=columns["rpm"][i],
            normalized_pos=columns["normalized_pos"][i],
            world_x=columns.get("world_x", [0.0] * n)[i],
            world_y=columns.get("world_y", [0.0] * n)[i],
            world_z=columns.get("world_z", [0.0] * n)[i],
            g_lateral=columns["g_lateral"][i],
            g_longitudinal=columns["g_longitudinal"][i],
            fuel=columns["fuel"][i],
            current_lap=int(columns["current_lap"][i]),
            lap_time_ms=int(columns["lap_time_ms"][i]),
            is_in_pit=bool(columns["is_in_pit"][i]),
            tire_temp_core=[tire_data["tire_temp_core"][c][i] for c in range(4)],
            tire_pressure=[tire_data["tire_pressure"][c][i] for c in range(4)],
            wheel_slip=[tire_data["wheel_slip"][c][i] for c in range(4)],
        )
        frames.append(frame.to_dict())

        # Detect lap boundary → record the completed lap
        cur_lap = int(columns["current_lap"][i])
        if cur_lap != prev_lap and cur_lap > prev_lap:
            # The lap that just ended is prev_lap
            # "Last Lap Time" at this sample tells us the completed lap time
            if ld.has("Last Lap Time"):
                last_lap_vals = _decode_or_zeros(ld, "Last Lap Time")
                lap_time_s = last_lap_vals[i]
            else:
                lap_time_s = columns["lap_time_ms"][i - 1] / 1000.0 if i > 0 else 0

            lap_time_ms = int(round(lap_time_s * 1000))
            if lap_time_ms > 0:
                session_store.add_lap(
                    session_id=session_id,
                    lap_number=prev_lap,
                    lap_time_ms=lap_time_ms,
                )
                logger.info(
                    "  Lap %d: %.3fs",
                    prev_lap,
                    lap_time_ms / 1000.0,
                )
            prev_lap = cur_lap

    # Write all frames
    telemetry_store.append_frames(session_id, frames)

    # End session
    session_store.end_session(session_id)

    laps = session_store.get_laps(session_id)
    logger.info(
        "Imported %s: track=%s car=%s laps=%d samples=%d",
        ld_path.name, track, car, len(laps), n,
    )
    return session_id
