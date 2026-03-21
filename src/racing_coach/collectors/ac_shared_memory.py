"""Assetto Corsa shared memory telemetry collector.

Uses ctypes to read AC's shared memory on Windows.
Based on the sim_info.py approach from the AC modding community.
"""

from __future__ import annotations

import asyncio
import ctypes
import logging
import time

from .base import TelemetryCollector
from .models import TelemetryFrame

logger = logging.getLogger(__name__)

# --- AC Shared Memory Structures ---
# Reference: AC SDK docs / sim_info.py


class ACVector3f(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float), ("z", ctypes.c_float)]


class ACPhysics(ctypes.Structure):
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("gas", ctypes.c_float),
        ("brake", ctypes.c_float),
        ("fuel", ctypes.c_float),
        ("gear", ctypes.c_int),
        ("rpms", ctypes.c_int),
        ("steerAngle", ctypes.c_float),
        ("speedKmh", ctypes.c_float),
        ("velocity", ctypes.c_float * 3),
        ("accG", ctypes.c_float * 3),
        ("wheelSlip", ctypes.c_float * 4),
        ("wheelLoad", ctypes.c_float * 4),
        ("wheelsPressure", ctypes.c_float * 4),
        ("wheelAngularSpeed", ctypes.c_float * 4),
        ("tyrewear", ctypes.c_float * 4),
        ("tyreDirtyLevel", ctypes.c_float * 4),
        ("tyreCoreTemperature", ctypes.c_float * 4),
        ("camberRAD", ctypes.c_float * 4),
        ("suspensionTravel", ctypes.c_float * 4),
        ("drs", ctypes.c_float),
        ("tc", ctypes.c_float),
        ("heading", ctypes.c_float),
        ("pitch", ctypes.c_float),
        ("roll", ctypes.c_float),
        ("cgHeight", ctypes.c_float),
        ("carDamage", ctypes.c_float * 5),
        ("numberOfTyresOut", ctypes.c_int),
        ("pitLimiterOn", ctypes.c_int),
        ("abs", ctypes.c_float),
    ]


class ACGraphics(ctypes.Structure):
    _fields_ = [
        ("packetId", ctypes.c_int),
        ("status", ctypes.c_int),  # AC_OFF=0, AC_REPLAY=1, AC_LIVE=2, AC_PAUSE=3
        ("session", ctypes.c_int),
        ("currentTime", ctypes.c_wchar * 15),
        ("lastTime", ctypes.c_wchar * 15),
        ("bestTime", ctypes.c_wchar * 15),
        ("split", ctypes.c_wchar * 15),
        ("completedLaps", ctypes.c_int),
        ("position", ctypes.c_int),
        ("iCurrentTime", ctypes.c_int),
        ("iLastTime", ctypes.c_int),
        ("iBestTime", ctypes.c_int),
        ("sessionTimeLeft", ctypes.c_float),
        ("distanceTraveled", ctypes.c_float),
        ("isInPit", ctypes.c_int),
        ("currentSectorIndex", ctypes.c_int),
        ("lastSectorTime", ctypes.c_int),
        ("numberOfLaps", ctypes.c_int),
        ("tyreCompound", ctypes.c_wchar * 33),
        ("replayTimeMultiplier", ctypes.c_float),
        ("normalizedCarPosition", ctypes.c_float),
        ("carCoordinates", ctypes.c_float * 3),
    ]


class ACSharedMemoryCollector(TelemetryCollector):
    """Reads telemetry from Assetto Corsa's shared memory (Windows only)."""

    def __init__(self, sample_rate_hz: int = 100):
        self._sample_rate_hz = sample_rate_hz
        self._interval = 1.0 / sample_rate_hz
        self._connected = False
        self._physics_map = None
        self._graphics_map = None

    async def connect(self) -> None:
        try:
            import mmap

            self._physics_map = mmap.mmap(-1, ctypes.sizeof(ACPhysics), "acpmf_physics")
            self._graphics_map = mmap.mmap(-1, ctypes.sizeof(ACGraphics), "acpmf_graphics")
            self._connected = True
            logger.info("Connected to AC shared memory")
        except Exception as e:
            logger.error("Failed to connect to AC shared memory: %s", e)
            raise

    async def disconnect(self) -> None:
        self._connected = False
        if self._physics_map:
            self._physics_map.close()
        if self._graphics_map:
            self._graphics_map.close()
        logger.info("Disconnected from AC shared memory")

    def is_connected(self) -> bool:
        return self._connected

    def _read_physics(self) -> ACPhysics:
        self._physics_map.seek(0)
        buf = self._physics_map.read(ctypes.sizeof(ACPhysics))
        return ACPhysics.from_buffer_copy(buf)

    def _read_graphics(self) -> ACGraphics:
        self._graphics_map.seek(0)
        buf = self._graphics_map.read(ctypes.sizeof(ACGraphics))
        return ACGraphics.from_buffer_copy(buf)

    async def read_frame(self) -> TelemetryFrame | None:
        if not self._connected:
            return None

        await asyncio.sleep(self._interval)

        physics = self._read_physics()
        graphics = self._read_graphics()

        # AC status 2 = LIVE
        if graphics.status != 2:
            return None

        return TelemetryFrame(
            timestamp_ms=time.time() * 1000,
            throttle=physics.gas,
            brake=physics.brake,
            steering=physics.steerAngle / 450.0,  # normalize to -1..1 (typical max lock)
            gear=physics.gear - 1,  # AC: 0=reverse, 1=neutral, 2=first
            speed_kmh=physics.speedKmh,
            rpm=float(physics.rpms),
            normalized_pos=graphics.normalizedCarPosition,
            world_x=graphics.carCoordinates[0],
            world_y=graphics.carCoordinates[1],
            world_z=graphics.carCoordinates[2],
            g_lateral=physics.accG[0],
            g_longitudinal=physics.accG[2],
            tire_temp_core=list(physics.tyreCoreTemperature),
            tire_pressure=list(physics.wheelsPressure),
            wheel_slip=list(physics.wheelSlip),
            fuel=physics.fuel,
            current_lap=graphics.completedLaps,
            lap_time_ms=graphics.iCurrentTime,
            is_in_pit=bool(graphics.isInPit),
        )
