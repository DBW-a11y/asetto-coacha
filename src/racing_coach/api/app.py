"""FastAPI application setup."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ..config import AppConfig, load_config
from ..coach.coach import Coach
from ..coach.llm_client import LLMClient
from ..coach.prompt_builder import PromptBuilder
from ..storage.session_store import SessionStore
from ..storage.telemetry_store import TelemetryStore
from .routes import sessions, telemetry, analysis, coaching, live


def create_app(config: AppConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if config is None:
        config = load_config()

    app = FastAPI(title="Racing Coach", version="0.1.0")

    # CORS for local dev
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize services
    data_dir = config.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    session_store = SessionStore(data_dir / config.storage.db_name)
    telemetry_store = TelemetryStore(data_dir / config.storage.parquet_dir)

    cache_dir = data_dir / "llm_cache" if config.coach.cache_responses else None
    llm_client = LLMClient(
        provider=config.coach.provider,
        model=config.coach.model,
        max_tokens=config.coach.max_tokens,
        cache_dir=cache_dir,
    )
    coach = Coach(session_store, telemetry_store, llm_client)

    # Store in app state for dependency injection
    app.state.config = config
    app.state.session_store = session_store
    app.state.telemetry_store = telemetry_store
    app.state.coach = coach

    # Register routes
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(telemetry.router, prefix="/api/telemetry", tags=["telemetry"])
    app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
    app.include_router(coaching.router, prefix="/api/coaching", tags=["coaching"])
    app.include_router(live.router, prefix="/api/live", tags=["live"])

    # Serve static UI files if built
    ui_dist = Path(__file__).parent.parent / "ui" / "dist"
    if ui_dist.exists():
        app.mount("/", StaticFiles(directory=str(ui_dist), html=True), name="ui")

    return app
