import asyncio
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
import uuid
import time
import logging

logger = logging.getLogger(__name__)

class StreamEvent(BaseModel):
    eventId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    agentName: str
    eventType: Literal["thought_start", "thought_delta", "thought_end", "tool_call", "tool_output"]
    payload: Dict[str, Any]
    traceId: str
    spanId: str
    parentSpanId: str | None = None

class EventQueue:
    _instance = None
    _queue = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventQueue, cls).__new__(cls)
            cls._queue = asyncio.Queue()
        return cls._instance

    def get_queue(self) -> asyncio.Queue:
        return self._queue

    def put_nowait(self, event: Dict[str, Any]):
        """Synchronous, non-blocking put for use in sync contexts"""
        try:
            self._queue.put_nowait(event)
            # Handle both dict and Pydantic model
            if isinstance(event, dict):
                event_type = event.get('eventType', 'unknown')
            else:
                # If it's a Pydantic model, access the attribute directly
                event_type = getattr(event, 'eventType', 'unknown')
            logger.debug(f"Event queued: {event_type}")
        except asyncio.QueueFull:
            # Handle both dict and Pydantic model
            if isinstance(event, dict):
                event_type = event.get('eventType', 'unknown')
            else:
                # If it's a Pydantic model, access the attribute directly
                event_type = getattr(event, 'eventType', 'unknown')
            logger.warning(f"Queue full, dropping event: {event_type}")

    async def put(self, event: Dict[str, Any]):
        """Async put for use in async contexts"""
        await self._queue.put(event)
        # Handle both dict and Pydantic model
        if isinstance(event, dict):
            event_type = event.get('eventType', 'unknown')
        else:
            # If it's a Pydantic model, access the attribute directly
            event_type = getattr(event, 'eventType', 'unknown')
        logger.debug(f"Event queued (async): {event_type}")

    async def get(self) -> Dict[str, Any]:
        return await self._queue.get()

# Singleton instance
event_queue = EventQueue()