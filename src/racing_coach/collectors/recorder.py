"""Records telemetry frames to storage."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from .models import TelemetryFrame

if TYPE_CHECKING:
    from ..storage.session_store import SessionStore
    from ..storage.telemetry_store import TelemetryStore
    from .base import TelemetryCollector

logger = logging.getLogger(__name__)


class TelemetryRecorder:
    """Buffers telemetry frames and writes them to storage periodically."""

    def __init__(
        self,
        collector: TelemetryCollector,
        session_store: SessionStore,
        telemetry_store: TelemetryStore,
        flush_interval_s: float = 5.0,
        buffer_size: int = 1000,
    ):
        self._collector = collector
        self._session_store = session_store
        self._telemetry_store = telemetry_store
        self._flush_interval = flush_interval_s
        self._buffer_size = buffer_size
        self._buffer: list[dict] = []
        self._session_id: str | None = None
        self._running = False
        self._last_lap = -1
        self._last_lap_time_ms: int = 0

    async def start(self, track: str = "unknown", car: str = "unknown") -> str:
        """Start recording a session. Returns the session ID."""
        self._session_id = self._session_store.create_session(track=track, car=car)
        self._running = True
        self._last_lap = -1
        logger.info("Started recording session %s (track=%s, car=%s)",
                     self._session_id, track, car)
        return self._session_id

    async def stop(self) -> None:
        """Stop recording and flush remaining data."""
        self._running = False
        await self._flush()
        if self._session_id:
            self._session_store.end_session(self._session_id)
            logger.info("Stopped recording session %s", self._session_id)

    async def run(self, track: str = "unknown", car: str = "unknown") -> None:
        """Main recording loop: collect frames until collector disconnects."""
        session_id = await self.start(track=track, car=car)
        flush_task = asyncio.create_task(self._periodic_flush())

        try:
            async for frame in self._collector.stream():
                if not self._running:
                    break
                self._process_frame(frame)
        finally:
            self._running = False
            flush_task.cancel()
            await self._flush()
            self._session_store.end_session(session_id)

    def _process_frame(self, frame: TelemetryFrame) -> None:
        """Process a single frame: detect lap changes, buffer data."""
        # Detect lap change — use the *previous* frame's lap_time_ms
        # because the current frame's lap_time_ms has already reset for the new lap
        if frame.current_lap != self._last_lap and self._last_lap >= 0:
            lap_time_ms = self._last_lap_time_ms if self._last_lap_time_ms > 0 else None
            if lap_time_ms and self._session_id:
                self._session_store.add_lap(
                    session_id=self._session_id,
                    lap_number=self._last_lap,
                    lap_time_ms=lap_time_ms,
                )
                logger.info("Lap %d completed: %.3fs", self._last_lap, lap_time_ms / 1000)
        self._last_lap = frame.current_lap
        self._last_lap_time_ms = frame.lap_time_ms

        self._buffer.append(frame.to_dict())

        if len(self._buffer) >= self._buffer_size:
            asyncio.get_event_loop().create_task(self._flush())

    async def _flush(self) -> None:
        """Write buffered frames to Parquet storage."""
        if not self._buffer or not self._session_id:
            return

        frames = self._buffer.copy()
        self._buffer.clear()

        self._telemetry_store.append_frames(self._session_id, frames)
        logger.debug("Flushed %d frames for session %s", len(frames), self._session_id)

    async def _periodic_flush(self) -> None:
        """Periodically flush the buffer."""
        while self._running:
            await asyncio.sleep(self._flush_interval)
            await self._flush()
