"""Abstract interface for telemetry collectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from .models import TelemetryFrame


class TelemetryCollector(ABC):
    """Base class for all telemetry collectors."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the telemetry source."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Clean up connection resources."""

    @abstractmethod
    async def read_frame(self) -> TelemetryFrame | None:
        """Read a single telemetry frame. Returns None if no data available."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the collector is currently connected."""

    async def stream(self) -> AsyncIterator[TelemetryFrame]:
        """Yield telemetry frames continuously."""
        while self.is_connected():
            frame = await self.read_frame()
            if frame is not None:
                yield frame

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *exc):
        await self.disconnect()
