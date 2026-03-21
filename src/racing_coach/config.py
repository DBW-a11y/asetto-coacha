"""Configuration management for Racing Coach."""

from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]
import sys
from dataclasses import dataclass, field
from pathlib import Path

if getattr(sys, 'frozen', False):
    _PROJECT_ROOT = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    _PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CONFIG = _PROJECT_ROOT / "config" / "default.toml"


@dataclass
class CollectorConfig:
    type: str = "mock"
    sample_rate_hz: int = 100
    buffer_size: int = 1000


@dataclass
class StorageConfig:
    parquet_dir: str = "telemetry"
    db_name: str = "sessions.db"


@dataclass
class AnalysisConfig:
    min_lap_time_s: int = 30
    max_lap_time_s: int = 600
    corner_speed_threshold_pct: float = 0.85
    smoothing_window: int = 5


@dataclass
class CoachConfig:
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    language: str = "zh-CN"
    max_tokens: int = 2000
    cache_responses: bool = True


@dataclass
class ApiConfig:
    host: str = "127.0.0.1"
    port: int = 8000


@dataclass
class AppConfig:
    data_dir: Path = field(default_factory=lambda: Path.home() / ".racing-coach" / "data")
    log_level: str = "INFO"
    collector: CollectorConfig = field(default_factory=CollectorConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    coach: CoachConfig = field(default_factory=CoachConfig)
    api: ApiConfig = field(default_factory=ApiConfig)


def load_config(path: Path | None = None) -> AppConfig:
    """Load configuration from TOML file, falling back to defaults."""
    config_path = path or _DEFAULT_CONFIG
    if not config_path.exists():
        return AppConfig()

    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    general = raw.get("general", {})
    data_dir = Path(general.get("data_dir", "~/.racing-coach/data")).expanduser()

    return AppConfig(
        data_dir=data_dir,
        log_level=general.get("log_level", "INFO"),
        collector=CollectorConfig(**raw.get("collector", {})),
        storage=StorageConfig(**raw.get("storage", {})),
        analysis=AnalysisConfig(**raw.get("analysis", {})),
        coach=CoachConfig(**raw.get("coach", {})),
        api=ApiConfig(**raw.get("api", {})),
    )
