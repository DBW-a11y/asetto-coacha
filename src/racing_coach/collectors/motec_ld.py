"""MoTeC i2 .ld file parser.

Pure struct-based parser for MoTeC LD telemetry files exported by
Assetto Corsa / ACC.  No external dependencies beyond the stdlib.

Binary format is reverse-engineered; see https://github.com/gotzl/ldparser
for prior art.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path


def _read_cstr(buf: bytes, offset: int, length: int) -> str:
    """Read a null-terminated string from *buf* at *offset*."""
    raw = buf[offset : offset + length]
    return raw.split(b"\x00", 1)[0].decode("latin-1")


# ---------------------------------------------------------------------------
# Channel descriptor
# ---------------------------------------------------------------------------

@dataclass
class LdChannel:
    name: str
    short_name: str
    unit: str
    freq: int
    data_ptr: int
    data_len: int          # number of samples
    dtype_a: int           # 0/3/5 → int, 7 → float
    dtype_b: int           # 2 → int16, 4 → int32
    shift: int
    mul: int
    scale: int
    dec: int

    @property
    def sample_size(self) -> int:
        if self.dtype_a == 7:
            return 4  # float32
        return self.dtype_b  # 2 or 4

    # --- Channel meta struct (116 bytes) ---
    #  0  I  prev_ptr
    #  4  I  next_ptr
    #  8  I  data_ptr
    # 12  I  n_data (sample count)
    # 16  H  counter
    # 18  H  dtype_a
    # 20  H  dtype_b
    # 22  H  freq
    # 24  h  shift
    # 26  h  mul
    # 28  h  scale
    # 30  h  dec
    # 32  32s name
    # 64  8s  short_name
    # 72  12s unit
    # 84  32x padding
    _STRUCT = struct.Struct("<IIII H HHH hhhh 32s 8s 12s 32x")

    @classmethod
    def from_bytes(cls, buf: bytes, offset: int) -> tuple[LdChannel, int]:
        """Parse one channel entry.  Returns ``(channel, next_ptr)``."""
        vals = cls._STRUCT.unpack_from(buf, offset)
        prev, nxt, data_ptr, n_data = vals[0:4]
        counter = vals[4]
        dtype_a, dtype_b, freq = vals[5:8]
        shift, mul, scale, dec = vals[8:12]
        name = vals[12].split(b"\x00", 1)[0].decode("latin-1")
        short = vals[13].split(b"\x00", 1)[0].decode("latin-1")
        unit = vals[14].split(b"\x00", 1)[0].decode("latin-1")
        ch = cls(
            name=name,
            short_name=short,
            unit=unit,
            freq=freq,
            data_ptr=data_ptr,
            data_len=n_data,
            dtype_a=dtype_a,
            dtype_b=dtype_b,
            shift=shift,
            mul=mul,
            scale=scale,
            dec=dec,
        )
        return ch, nxt


# ---------------------------------------------------------------------------
# LD file
# ---------------------------------------------------------------------------

# Header layout (offsets in bytes):
#   0   I   marker
#   4   4x
#   8   I   chann_meta_ptr
#  12   I   chann_data_ptr
#  16   20x
#  36   I   event_ptr
#  40   24x
#  64   HHH (static)
#  70   I   device_serial
#  74   8s  device_type
#  82   H   device_version
#  84   H   (static)
#  86   I   num_channs
#  90   4x
#  94   16s date
# 110   16x
# 126   16s time
# 142   16x
# 158   64s driver
# 222   64s vehicle
# 286   64x
# 350   64s venue
_HDR = struct.Struct(
    "<"
    "I 4x"
    "II"
    "20x"
    "I"
    "24x"
    "HHH"
    "I"
    "8s"
    "H"
    "H"
    "I"
    "4x"
    "16s"
    "16x"
    "16s"
    "16x"
    "64s"
    "64s"
    "64x"
    "64s"
)


@dataclass
class LdFile:
    driver: str
    vehicle: str
    venue: str
    date: str
    time: str
    channels: dict[str, LdChannel]
    _buf: bytes  # keep the raw data for decoding

    # ----- decode helpers -------------------------------------------------

    def decode_channel(self, ch: LdChannel) -> list[float]:
        """Decode raw samples into physical values.

        Formula (from reverse-engineered format):
            value = (raw / scale) * 10**(-dec) + shift) * mul
        """
        n = ch.data_len
        offset = ch.data_ptr

        if ch.dtype_a == 7:
            # float32
            raw = struct.unpack_from(f"<{n}f", self._buf, offset)
            return list(raw)

        if ch.dtype_b == 4:
            fmt = f"<{n}i"
        else:
            fmt = f"<{n}h"

        raw = struct.unpack_from(fmt, self._buf, offset)

        scale = ch.scale if ch.scale != 0 else 1
        mul = ch.mul if ch.mul != 0 else 1
        factor = mul * (10.0 ** (-ch.dec)) / scale
        shift = ch.shift * mul

        return [v * factor + shift for v in raw]

    def decode(self, name: str) -> list[float]:
        """Decode channel by name.  Raises ``KeyError`` if missing."""
        return self.decode_channel(self.channels[name])

    def has(self, name: str) -> bool:
        return name in self.channels

    @property
    def num_samples(self) -> int:
        """Number of samples (from the first channel)."""
        if not self.channels:
            return 0
        return next(iter(self.channels.values())).data_len

    @property
    def sample_rate(self) -> int:
        if not self.channels:
            return 20
        return next(iter(self.channels.values())).freq

    # ----- parsing --------------------------------------------------------

    @classmethod
    def from_file(cls, path: str | Path) -> LdFile:
        path = Path(path)
        buf = path.read_bytes()
        return cls.from_bytes(buf)

    @classmethod
    def from_bytes(cls, buf: bytes) -> LdFile:
        vals = _HDR.unpack_from(buf, 0)
        # vals indices:
        #  0=marker, 1=meta_ptr, 2=data_ptr, 3=event_ptr,
        #  4,5,6=static HHH, 7=serial, 8=device_type,
        #  9=dev_ver, 10=static, 11=num_channs,
        #  12=date, 13=time, 14=driver, 15=vehicle, 16=venue
        meta_ptr = vals[1]
        date = vals[12].split(b"\x00", 1)[0].decode("latin-1")
        time_ = vals[13].split(b"\x00", 1)[0].decode("latin-1")
        driver = vals[14].split(b"\x00", 1)[0].decode("latin-1")
        vehicle = vals[15].split(b"\x00", 1)[0].decode("latin-1")
        venue = vals[16].split(b"\x00", 1)[0].decode("latin-1")

        # Walk the channel linked list
        channels: dict[str, LdChannel] = {}
        pos = meta_ptr
        while pos != 0:
            ch, nxt = LdChannel.from_bytes(buf, pos)
            channels[ch.name] = ch
            pos = nxt

        return cls(
            driver=driver,
            vehicle=vehicle,
            venue=venue,
            date=date,
            time=time_,
            channels=channels,
            _buf=buf,
        )
