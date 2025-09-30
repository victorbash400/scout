
from typing import Any
import uuid
from utils.event_queue import event_queue, StreamEvent
import logging
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import BeforeInvocationEvent, AfterInvocationEvent, MessageAddedEvent

logger = logging.getLogger(__name__)

class StreamingCallbackHandler:
    def __init__(self, agent_name: str, trace_id: str, parent_span_id: str):
        self.agent_name = agent_name
        self.trace_id = trace_id
        self.parent_span_id = parent_span_id
        logger.info(f"StreamingCallbackHandler initialized for {agent_name}")

    async def on_thought_start(self) -> str:
        span_id = str(uuid.uuid4())
        event = StreamEvent(
            agentName=self.agent_name,
            eventType="thought_start",
            payload={},
            traceId=self.trace_id,
            spanId=span_id,
            parentSpanId=self.parent_span_id,
        )
        await event_queue.put(event)
        logger.info(f"Event sent: {event.eventType} for {self.agent_name}")
        return span_id

    async def on_thought_delta(self, text: str, span_id: str):
        event = StreamEvent(
            agentName=self.agent_name,
            eventType="thought_delta",
            payload={"text": text},
            traceId=self.trace_id,
            spanId=span_id,
            parentSpanId=self.parent_span_id,
        )
        await event_queue.put(event)

    async def on_thought_end(self, span_id: str):
        event = StreamEvent(
            agentName=self.agent_name,
            eventType="thought_end",
            payload={},
            traceId=self.trace_id,
            spanId=span_id,
            parentSpanId=self.parent_span_id,
        )
        await event_queue.put(event)
        logger.info(f"Event sent: {event.eventType} for {self.agent_name}")

    async def on_tool_call(self, tool_name: str, tool_input: dict) -> str:
        span_id = str(uuid.uuid4())
        event = StreamEvent(
            agentName=self.agent_name,
            eventType="tool_call",
            payload={"tool_name": tool_name, "tool_input": tool_input},
            traceId=self.trace_id,
            spanId=span_id,
            parentSpanId=self.parent_span_id,
        )
        await event_queue.put(event)
        logger.info(f"Event sent: {event.eventType} for {self.agent_name} - {tool_name}")
        return span_id

    async def on_tool_output(self, output: str, span_id: str):
        event = StreamEvent(
            agentName=self.agent_name,
            eventType="tool_output",
            payload={"output": output},
            traceId=self.trace_id,
            spanId=span_id,
            parentSpanId=self.parent_span_id,
        )
        await event_queue.put(event)
        logger.info(f"Event sent: {event.eventType} for {self.agent_name}")
