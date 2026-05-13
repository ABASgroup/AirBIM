"""
Async runtime utilities for Celery worker processes.

Keeps one dedicated event loop per worker process to avoid loop-mismatch
issues with async DB drivers and pooled connections.
"""

from __future__ import annotations

import asyncio
from typing import Awaitable, TypeVar


T = TypeVar("T")


class _RuntimeState:
    worker_loop: asyncio.AbstractEventLoop | None = None


_state = _RuntimeState()


def init_worker_event_loop() -> None:
    """Initialize a dedicated event loop for current worker process."""
    if _state.worker_loop is not None and not _state.worker_loop.is_closed():
        return

    _state.worker_loop = asyncio.new_event_loop()


def close_worker_event_loop() -> None:
    """Close dedicated worker loop on process shutdown."""
    if _state.worker_loop is None:
        return

    if not _state.worker_loop.is_closed():
        _state.worker_loop.close()

    _state.worker_loop = None


def run_async(awaitable: Awaitable[T]) -> T:
    """Run coroutine in worker-dedicated loop."""
    if _state.worker_loop is None or _state.worker_loop.is_closed():
        init_worker_event_loop()

    loop = _state.worker_loop
    if loop is None:
        raise RuntimeError("Worker event loop is not initialized")

    return loop.run_until_complete(awaitable)
