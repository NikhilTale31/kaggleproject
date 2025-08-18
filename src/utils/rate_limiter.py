import asyncio
import time
from typing import Optional


class AsyncRateLimiter:
    """Simple async rate limiter for API calls."""
    
    def __init__(self, rate_limit: int = 100, per_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            rate_limit: Maximum number of requests
            per_seconds: Time window in seconds
        """
        self.rate_limit = rate_limit
        self.per_seconds = per_seconds
        self.calls = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait if necessary to respect rate limit."""
        async with self._lock:
            now = time.time()
            # Remove old calls outside the window
            self.calls = [call_time for call_time in self.calls 
                         if call_time > now - self.per_seconds]
            
            if len(self.calls) >= self.rate_limit:
                # Need to wait
                sleep_time = self.calls[0] + self.per_seconds - now
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    # Recursive call to recheck
                    await self.acquire()
                    return
            
            # Add current call
            self.calls.append(now)


__all__ = ["AsyncRateLimiter"]
