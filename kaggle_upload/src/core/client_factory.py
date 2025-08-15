from __future__ import annotations

import logging
from typing import Any

from ..config import Config
from ..api_client import APIClient

try:
    from ..backends.hf_local import HFLocalClient
except Exception:
    HFLocalClient = None  # type: ignore


_logger = logging.getLogger("client-factory")


def create_client(config: Config) -> Any:
    """
    Return a client instance that supports async context and .generate() with the same signature
    as APIClient. Selection is based on config.backend.

    backends:
      - "openai": use APIClient (OpenAI-compatible HTTP API)
      - "hf_local": use transformers local backend (HFLocalClient)
    """
    backend = getattr(config, "backend", None) or "hf_local"
    backend = str(backend).lower()

    if backend == "openai":
        return APIClient(config)

    if backend == "hf_local":
        if HFLocalClient is None:
            raise RuntimeError("HFLocalClient not available. Install transformers to use hf_local backend.")
        return HFLocalClient(config)

    _logger.warning(f"Unknown backend '{backend}', defaulting to hf_local")
    if HFLocalClient is None:
        raise RuntimeError("HFLocalClient not available. Install transformers to use hf_local backend.")
    return HFLocalClient(config)
