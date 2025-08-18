from __future__ import annotations

import logging
from typing import Any

from ..config import Config
from ..api_client import APIClient

# Import mock client instead of hf_local
from ..backends.mock_client import MockClient

_logger = logging.getLogger("client-factory")


class ClientFactory:
    """Factory class for creating client instances."""
    
    @staticmethod
    def create_client(config: Config) -> Any:
        """
        Return a client instance that supports async context and .generate().
        
        backends:
          - "openai": use APIClient (OpenAI-compatible HTTP API)
          - "mock": use MockClient (no external dependencies)
        """
        backend = getattr(config, "backend", None) or "mock"
        backend = str(backend).lower()

        if backend == "openai":
            return APIClient(config)

        if backend == "mock":
            return MockClient(config)

        _logger.warning(f"Unknown backend '{backend}', defaulting to mock")
        return MockClient(config)


# Keep the original function for backward compatibility
create_client = ClientFactory.create_client
