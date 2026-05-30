import asyncio
import json
import logging
from typing import Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)
        logger.info(f"WebSocket connected. Total: {len(self.active)}")

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)
        logger.info(f"WebSocket disconnected. Total: {len(self.active)}")

    async def broadcast(self, data: dict):
        if not self.active:
            return
        message = json.dumps(data)
        dead = set()
        for ws in self.active:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.active.discard(ws)


manager = ConnectionManager()


def broadcast_sync(data: dict):
    """
    Called from synchronous Celery worker context.
    Schedules the async broadcast on the event loop if available.
    """
    if manager._loop and not manager._loop.is_closed():
        asyncio.run_coroutine_threadsafe(manager.broadcast(data), manager._loop)
