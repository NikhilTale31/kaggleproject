from __future__ import annotations

import asyncio
import hashlib
import json
import os
from typing import Any, Dict, Optional

import httpx

from .config import Config
from .utils.rate_limiter import AsyncRateLimiter
from .utils.file_manager import read_json, write_json
from .utils.logger import get_logger, log_exception


class APIClient:
    """
    Async API client wrapping httpx with:
      - Concurrency limiting
      - Request rate limiting (per 60s window)
      - On-disk caching
      - Simple retries with exponential backoff
      - Normalized text extraction

    The client targets an OpenAI-compatible chat/completions endpoint by default.
    """

    def __init__(self, config: Config, logger_name: str = "api-client") -> None:
        self.config = config
        self.logger = get_logger(logger_name)
        self._limiter = AsyncRateLimiter(
            rate_per_min=config.rate_limit_per_min, max_concurrent=config.max_concurrent
        )
        self._client: Optional[httpx.AsyncClient] = None
        self._cache_enabled = bool(config.cache_enabled)
        self._cache_dir = config.cache_dir
        if self._cache_enabled and self._cache_dir:
            os.makedirs(self._cache_dir, exist_ok=True)

    async def __aenter__(self) -> "APIClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def start(self) -> None:
        if self._client is None:
            timeout = httpx.Timeout(self.config.request_timeout_seconds)
            # Base URL is not strictly necessary, but kept for clarity
            self._client = httpx.AsyncClient(timeout=timeout)
            self.logger.info("APIClient started")

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            self.logger.info("APIClient closed")

    def _cache_key(self, payload: Dict[str, Any]) -> str:
        m = hashlib.sha256()
        m.update(self.config.model.encode("utf-8"))
        m.update(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8"))
        return m.hexdigest()

    def _cache_path(self, key: str) -> str:
        return os.path.join(self._cache_dir, f"{key}.json")

    def _load_cache(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            path = self._cache_path(key)
            if os.path.isfile(path):
                return read_json(path)
        except Exception as e:
            self.logger.warning(f"Cache read failed for key={key}: {e}")
        return None

    def _save_cache(self, key: str, data: Dict[str, Any]) -> None:
        try:
            path = self._cache_path(key)
            write_json(path, data)
        except Exception as e:
            self.logger.warning(f"Cache write failed for key={key}: {e}")

    def _extract_output_text(self, data: Dict[str, Any]) -> str:
        """
        Attempt to normalize an LLM response into a single output text.
        Works with OpenAI chat/completions style responses.
        """
        try:
            choices = data.get("choices", [])
            if choices:
                msg = choices[0].get("message") or {}
                content = msg.get("content")
                if isinstance(content, str):
                    return content
            # fallback to 'text' style responses
            if "text" in data and isinstance(data["text"], str):
                return data["text"]
        except Exception:
            pass
        return ""

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        tools: Optional[list] = None,
        metadata: Optional[dict] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Submit a prompt to the model and return a response dict:
          {
            "output_text": str,  # normalized assistant message content
            "raw": dict,         # raw provider JSON
            "meta": { "cached": bool, "cache_key": str }
          }

        Caching:
          - Keyed by (model + payload JSON). If enabled and present, returns cached result.
        Retries:
          - On 429 / 5xx.
        """
        if self._client is None:
            await self.start()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": float(temperature),
        }
        if max_tokens is not None:
            payload["max_tokens"] = int(max_tokens)
        if tools:
            payload["tools"] = tools
        if metadata:
            payload["metadata"] = metadata

        cache_key = self._cache_key(payload)
        if self._cache_enabled:
            cached = self._load_cache(cache_key)
            if cached is not None:
                cached["meta"] = {"cached": True, "cache_key": cache_key}
                return cached

        # Build request
        headers = {
            "Content-Type": "application/json",
        }
        api_key = self.config.effective_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        url = f"{self.config.api_base.rstrip('/')}/chat/completions"

        attempt = 0
        max_attempts = max(1, int(self.config.retry_attempts))
        backoff = float(self.config.retry_backoff_seconds)

        while True:
            attempt += 1
            async with self._limiter:
                try:
                    assert self._client is not None
                    resp = await self._client.post(url, headers=headers, json=payload)
                except Exception as e:
                    if attempt >= max_attempts:
                        log_exception(self.logger, f"Request failed (attempt {attempt}/{max_attempts})", e)
                        raise
                    self.logger.warning(f"Transport error on attempt {attempt}/{max_attempts}: {e}. Retrying in {backoff:.2f}s")
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                    continue

            if resp.status_code >= 200 and resp.status_code < 300:
                try:
                    data = resp.json()
                except Exception as e:
                    log_exception(self.logger, "Failed to parse JSON response", e)
                    raise

                text = self._extract_output_text(data)
                result = {"output_text": text, "raw": data, "meta": {"cached": False, "cache_key": cache_key}}
                if self._cache_enabled:
                    self._save_cache(cache_key, result)
                return result

            # Retry on 429/5xx
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_attempts:
                self.logger.warning(
                    f"Server returned {resp.status_code} (attempt {attempt}/{max_attempts}). Retrying in {backoff:.2f}s"
                )
                await asyncio.sleep(backoff)
                backoff *= 2.0
                continue

            # Non-retryable or out of attempts
            try:
                body = resp.text
            except Exception:
                body = "<unavailable>"
            self.logger.error(f"Request failed with status={resp.status_code} body={body[:500]}")
            resp.raise_for_status()


__all__ = ["APIClient"]
