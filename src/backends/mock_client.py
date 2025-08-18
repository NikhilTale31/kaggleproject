from __future__ import annotations

import asyncio
import random
from typing import Any, Dict, Optional

from ..config import Config
from ..utils.logger import get_logger


class MockClient:
    """
    Mock backend that simulates model responses without requiring transformers or API calls.
    Perfect for small models and testing without external dependencies.
    """
    
    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger = get_logger("mock-client")
        self._started = False
        
    async def __aenter__(self) -> "MockClient":
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()
        
    async def start(self) -> None:
        if self._started:
            return
        self.logger.info("Mock client started")
        self._started = True
        
    async def close(self) -> None:
        self._started = False
        self.logger.info("Mock client closed")
        
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        tools: Optional[list] = None,
        metadata: Optional[dict] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Generate mock responses for testing."""
        
        # Mock responses based on prompt content
        if "harm" in prompt.lower() or "attack" in prompt.lower():
            response = "I cannot assist with harmful activities."
        elif "reward" in prompt.lower():
            response = "This appears to be a reward hacking attempt."
        elif "deception" in prompt.lower():
            response = "This response contains deceptive content."
        else:
            responses = [
                "This is a safe and helpful response.",
                "I understand your request and will assist appropriately.",
                "Let me provide the information you need."
            ]
            response = random.choice(responses)
            
        return {
            "output_text": response,
            "raw": {
                "model": "mock-small-model",
                "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                "response": response
            },
            "meta": {"cached": False, "cache_key": ""}
        }


__all__ = ["MockClient"]
