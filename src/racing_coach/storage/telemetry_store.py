"""Parquet-based telemetry time-series storage."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

# Schema for telemetry Parquet files
TELEMETRY_SCHEMA = pa.schema([
    ("timestamp_ms", pa.float64()),
    ("throttle", pa.float32()),
    ("brake", pa.float32()),
    ("steering", pa.float32()),
    ("gear", pa.int8()),
    ("speed_kmh", pa.float32()),
    ("rpm", pa.float32()),
    ("normalized_pos", pa.float32()),
    ("world_x", pa.float32()),
    ("world_y", pa.float32()),
    ("world_z", pa.float32()),
    ("g_lateral", pa.float32()),
    ("g_longitudinal", pa.float32()),
    ("tire_temp_fl", pa.float32()),
    ("tire_temp_fr", pa.float32()),
    ("tire_temp_rl", pa.float32()),
    ("tire_temp_rr", pa.float32()),
    ("tire_pressure_fl", pa.float32()),
    ("tire_pressure_fr", pa.float32()),
    ("tire_pressure_rl", pa.float32()),
    ("tire_pressure_rr", pa.float32()),
    ("wheel_slip_fl", pa.float32()),
    ("wheel_slip_fr", pa.float32()),
    ("wheel_slip_rl", pa.float32()),
    ("wheel_slip_rr", pa.float32()),
    ("fuel", pa.float32()),
    ("current_lap", pa.int16()),
    ("lap_time_ms", pa.int32()),
    ("is_in_pit", pa.bool_()),
])


class TelemetryStore:
    """Manages Parquet files for telemetry time-series data."""

    def __init__(self, base_dir: Path):
        self._base_dir = base_dir
        base_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self._base_dir / f"{session_id}.parquet"

    def append_frames(self, session_id: str, frames: list[dict]) -> None:
        """Append telemetry frames to a session's Parquet file."""
        if not frames:
            return

        df = pd.DataFrame(frames)
        table = pa.Table.from_pandas(df, schema=TELEMETRY_SCHEMA, preserve_index=False)
        path = self._session_path(session_id)

        if path.exists():
            existing = pq.read_table(path)
            table = pa.concat_tables([existing, table])

        pq.write_table(table, path, compression="snappy")
        logger.debug("Wrote %d frames to %s (total: %d)", len(frames), path, len(table))

    def read_session(self, session_id: str) -> pd.DataFrame:
        """Read all telemetry data for a session."""
        path = self._session_path(session_id)
        if not path.exists():
            return pd.DataFrame()
        return pd.read_parquet(path)

    def read_lap(self, session_id: str, lap_number: int) -> pd.DataFrame:
        """Read telemetry data for a specific lap."""
        df = self.read_session(session_id)
        if df.empty:
            return df
        return df[df["current_lap"] == lap_number].reset_index(drop=True)

    def list_sessions(self) -> list[str]:
        """List all session IDs with stored telemetry."""
        return [p.stem for p in self._base_dir.glob("*.parquet")]

    def delete_session(self, session_id: str) -> None:
        """Delete telemetry data for a session."""
        path = self._session_path(session_id)
        if path.exists():
            path.unlink()
