"""
API Client for OpenAI-compatible HTTP API and local backend integration.

This module provides the APIClient class for interacting with OpenAI-compatible APIs
and local backends for the vulnerability scanning competition.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import aiohttp
from aiohttp import ClientTimeout

from .config import Config

logger = logging.getLogger("api_client")


class APIClient:
    """
    Async HTTP client for OpenAI-compatible APIs.
    """

    def __init__(self, config: Config):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = config.api_base or "https://api.openai.com/v1"
        self.api_key = config.api_key
        self.model = config.model or "gpt-3.5-turbo"
        self.timeout = ClientTimeout(total=config.request_timeout_seconds or 60)

    async def start(self) -> None:
        """Start the aiohttp session."""
        if self.session is None:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=self.timeout,
            )

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def __aenter__(self) -> "APIClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        tools: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a response using the configured model.

        Args:
            prompt: The input prompt
            system: Optional system message
            tools: Optional tools for the model
            metadata: Optional metadata for tracking

        Returns:
            Dictionary containing the response and metadata
        """
        if not self.session:
            raise RuntimeError("Client not started. Use async context manager or call start() first.")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.95,
        }

        if tools:
            payload["tools"] = tools

        async with self.session.post(
            f"{self.base_url}/chat/completions",
            json=payload,
        ) as response:
            result = await response.json()
            return {
                "output_text": result["choices"][0]["message"]["content"],
                "meta": {
                    "cached": False,
                    "model": self.model,
                    "usage": result.get("usage", {}),
                    "metadata": metadata or {},
                },
            }
