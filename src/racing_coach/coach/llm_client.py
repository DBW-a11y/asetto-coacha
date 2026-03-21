"""LLM API client for the AI coach, supporting multiple providers."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMClient:
    """Multi-provider LLM client with response caching.

    Supported providers:
      - "anthropic": uses Anthropic SDK (requires ANTHROPIC_API_KEY)
      - "openai_compatible": uses OpenAI SDK against any compatible endpoint
        (requires LLM_API_KEY and LLM_BASE_URL, or provider-specific env vars)
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 2000,
        cache_dir: Path | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self._provider = provider
        self._model = model
        self._max_tokens = max_tokens
        self._cache_dir = cache_dir
        self._api_key = api_key
        self._base_url = base_url
        self._client = None
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, system: str, user: str) -> str:
        content = f"{self._model}:{system}:{user}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _get_cached(self, key: str) -> str | None:
        if not self._cache_dir:
            return None
        path = self._cache_dir / f"{key}.json"
        if path.exists():
            data = json.loads(path.read_text())
            return data.get("response")
        return None

    def _set_cached(self, key: str, response: str) -> None:
        if not self._cache_dir:
            return
        path = self._cache_dir / f"{key}.json"
        path.write_text(json.dumps({"response": response}))

    def _init_client(self):
        if self._provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(
                api_key=self._api_key or os.environ.get("ANTHROPIC_API_KEY"),
            )
        else:
            from openai import OpenAI
            api_key = self._api_key or os.environ.get("LLM_API_KEY", "")
            base_url = self._base_url or os.environ.get("LLM_BASE_URL", "")
            self._client = OpenAI(api_key=api_key, base_url=base_url)

    def _chat_anthropic(self, system: str, user: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text

    def _chat_openai_compatible(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content

    def chat(self, system: str, user: str, use_cache: bool = True) -> str:
        """Send a message to the LLM and get a response."""
        if use_cache:
            key = self._cache_key(system, user)
            cached = self._get_cached(key)
            if cached:
                logger.debug("Cache hit for LLM request")
                return cached

        if self._client is None:
            self._init_client()

        logger.info("Sending request to %s via %s", self._model, self._provider)
        try:
            if self._provider == "anthropic":
                text = self._chat_anthropic(system, user)
            else:
                text = self._chat_openai_compatible(system, user)
        except Exception as e:
            logger.error("LLM API error: %s", e)
            raise

        if use_cache:
            self._set_cached(key, text)

        return text
