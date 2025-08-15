import asyncio
from collections import deque
from time import monotonic
from typing import Deque, Optional


class AsyncRateLimiter:
    """
    Async rate limiter with concurrency control.

    - Enforces at most `rate_per_min` acquisitions per rolling 60s window.
    - Enforces at most `max_concurrent` concurrent acquisitions at any time.
    - Usable as an async context manager:
        limiter = AsyncRateLimiter(rate_per_min=100, max_concurrent=5)
        async with limiter:
            # perform a single API call within limits

    Notes:
    - Call acquire() to reserve a slot; call release() when done.
    - Using it as an async context manager calls acquire() on __aenter__
      and release() on __aexit__ automatically.
    """

    def __init__(self, rate_per_min: int, max_concurrent: int):
        if rate_per_min <= 0:
            raise ValueError("rate_per_min must be > 0")
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be > 0")

        self._rate_per_min = int(rate_per_min)
        self._window_seconds = 60.0
        self._sem = asyncio.Semaphore(int(max_concurrent))
        self._timestamps: Deque[float] = deque()
        self._lock = asyncio.Lock()

    @property
    def rate_per_min(self) -> int:
        return self._rate_per_min

    @property
    def max_concurrent(self) -> int:
        return self._sem._value + len(self._sem._waiters)  # type: ignore[attr-defined]

    async def acquire(self) -> None:
        """
        Acquire both concurrency permit and rate slot.
        This will block (await) until both constraints are satisfied.
        """
        await self._sem.acquire()
        try:
            await self._wait_for_rate_slot()
        except Exception:
            # If anything goes wrong, ensure semaphore is released.
            self._sem.release()
            raise

    def release(self) -> None:
        """
        Release the concurrency permit.
        """
        self._sem.release()

    async def _wait_for_rate_slot(self) -> None:
        """
        Wait until the number of timestamps in the last window is < rate_per_min,
        then append the current timestamp to reserve a slot.
        """
        while True:
            now = monotonic()
            async with self._lock:
                # prune old timestamps
                while self._timestamps and (now - self._timestamps[0]) > self._window_seconds:
                    self._timestamps.popleft()

                if len(self._timestamps) < self._rate_per_min:
                    # reserve a slot
                    self._timestamps.append(now)
                    return

                # need to wait until the oldest slot expires
                oldest = self._timestamps[0]
                sleep_for = max(0.0, (self._window_seconds - (now - oldest)) + 0.001)

            # cap sleep to avoid overly long sleeps in case of clock drift or changes
            await asyncio.sleep(min(sleep_for, 1.0))

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.release()
        # do not suppress exceptions
        return False


__all__ = ["AsyncRateLimiter"]
