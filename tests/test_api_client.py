import asyncio
import os
from typing import Any, Dict

import pytest

from src.config import Config
from src.api_client import APIClient


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: Dict[str, Any] | None = None):
        self.status_code = status_code
        self._payload = payload or {
            "id": "test",
            "object": "chat.completion",
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": "OK"}}
            ],
        }
        self.text = "OK"

    def json(self) -> Dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if not (200 <= self.status_code < 300):
            raise AssertionError(f"HTTP error: {self.status_code}")


class FakeClient:
    def __init__(self):
        self.calls = 0
        self.last_url = None
        self.last_headers = None
        self.last_json = None

    async def post(self, url, headers=None, json=None):
        self.calls += 1
        self.last_url = url
        self.last_headers = headers
        self.last_json = json
        return FakeResponse()

    async def aclose(self):
        return None


@pytest.mark.asyncio
async def test_api_client_caching_and_generate(tmp_path):
    cache_dir = tmp_path / "cache"
    os.makedirs(cache_dir, exist_ok=True)

    cfg = Config(
        api_key=None,
        api_base="https://example.invalid/v1",
        model="dummy-model",
        max_concurrent=2,
        rate_limit_per_min=1000,
        cache_enabled=True,
        cache_dir=str(cache_dir),
        request_timeout_seconds=10,
        retry_attempts=1,
        retry_backoff_seconds=0.01,
    )

    client = APIClient(cfg)
    await client.start()
    try:
        # inject fake transport
        fake = FakeClient()
        client._client = fake  # type: ignore[attr-defined]

        # First call: network (fake) should be used
        r1 = await client.generate(prompt="hello world")
        assert r1["output_text"] == "OK"
        assert r1["meta"]["cached"] is False
        assert fake.calls == 1

        # Second call: should be served from cache, no new network calls
        r2 = await client.generate(prompt="hello world")
        assert r2["output_text"] == "OK"
        assert r2["meta"]["cached"] is True
        assert fake.calls == 1
    finally:
        await client.close()
