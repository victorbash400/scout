import os
import asyncio
import logging
from typing import AsyncGenerator
from strands import Agent, tool
from strands.multiagent.a2a import A2AServer
from dotenv import load_dotenv
from config.settings import settings
import threading
import requests
import time
from datetime import datetime

# ------------------------
# Setup
# ------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------
# Mock Tool
# ------------------------
@tool
def mock_tool(task_name: str) -> str:
    """A placeholder tool that does nothing significant."""
    logger.info(f"Mock tool called with task: {task_name}")
    return f"Task '{task_name}' processed (mock)."

# ------------------------
# Improved Callback Handler
# ------------------------
class OrchestratorCallbackHandler:
    """Improved callback that properly handles streaming and tool events separately."""
    
    def __init__(self, webhook_url: str = "http://localhost:8000/api/orchestrator/events"):
        self.webhook_url = webhook_url
        self._current_tool_call = None
        self._text_buffer = ""
        self._in_tool_call = False

    def _post(self, payload: dict):
        """Send webhook payload in background thread"""
        def _do():
            try:
                requests.post(self.webhook_url, json=payload, timeout=5)
            except Exception as e:
                logger.debug(f"Webhook POST failed: {e}")
        threading.Thread(target=_do, daemon=True).start()

    def _send_event(self, event_type: str, message: str, extra_data: dict = None):
        """Send a single event to the webhook"""
        payload = {
            "type": "orchestrator_message",
            "event": event_type,
            "message": message,
            "extra": extra_data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        self._post(payload)

    def __call__(self, **kwargs):
        try:
            # Handle different event types from Strands streaming
            event_type = kwargs.get("event_type")
            
            # Tool call start
            if "tool_use" in kwargs or (event_type and "toolUse" in str(event_type)):
                tool_name = self._extract_tool_name(kwargs)
                if tool_name and not self._in_tool_call:
                    self._in_tool_call = True
                    self._current_tool_call = tool_name
                    self._send_event(
                        "tool_start",
                        f"Using {tool_name}...",
                        {"tool_name": tool_name}
                    )
                return

            # Tool call result/end
            elif "toolResult" in str(kwargs) or (self._in_tool_call and "result" in kwargs):
                if self._current_tool_call:
                    result = kwargs.get("result") or "Tool execution completed"
                    self._send_event(
                        "tool_end",
                        f"✓ {self._current_tool_call} completed",
                        {
                            "tool_name": self._current_tool_call,
                            "result": str(result)
                        }
                    )
                    self._current_tool_call = None
                    self._in_tool_call = False
                return

            # Text streaming - handle deltas/fragments
            elif not self._in_tool_call:
                text_content = self._extract_text_content(kwargs)
                if text_content:
                    # Buffer small fragments, send larger chunks
                    self._text_buffer += text_content
                    
                    # Send buffer when we have enough content or on sentence boundaries
                    if (len(self._text_buffer) > 50 or 
                        text_content.endswith(('.', '!', '?', '\n')) or
                        "final" in str(kwargs).lower()):
                        
                        if self._text_buffer.strip():
                            self._send_event(
                                "text_stream",
                                self._text_buffer.strip()
                            )
                            self._text_buffer = ""

        except Exception as e:
            logger.error(f"OrchestratorCallbackHandler error: {e}")

    def _extract_tool_name(self, kwargs):
        """Extract tool name from various event formats"""
        # Direct tool name
        if "tool_name" in kwargs:
            return kwargs["tool_name"]
        
        # Tool use object
        tool_use = kwargs.get("tool_use") or kwargs.get("toolUse")
        if tool_use and isinstance(tool_use, dict):
            return tool_use.get("name")
        
        # Check in nested structures
        for key, value in kwargs.items():
            if isinstance(value, dict) and "name" in value:
                return value["name"]
            if "tool" in key.lower() and isinstance(value, str):
                return value
        
        return None

    def _extract_text_content(self, kwargs):
        """Extract text content from various event formats"""
        # Direct text fields
        for field in ["text", "content", "delta", "message"]:
            if field in kwargs:
                value = kwargs[field]
                if isinstance(value, str):
                    return value
                elif isinstance(value, dict) and "text" in value:
                    return value["text"]
        
        # Check nested structures
        for key, value in kwargs.items():
            if isinstance(value, dict):
                for text_field in ["text", "content", "delta"]:
                    if text_field in value:
                        return str(value[text_field])
        
        return None

# ------------------------
# Orchestrator Agent
# ------------------------
class OrchestratorAgent:
    def __init__(self):
        # Load AWS credentials (optional)
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region
        logger.info("✅ AWS credentials loaded")

        # Agent setup with improved callback
        self.agent = Agent(
            name="SCOUT Orchestrator",
            description="Orchestrator Agent for receiving plans from Planner and coordinating.",
            model=settings.bedrock_model_id,
            system_prompt="""
You are the Orchestrator Agent. Your role:

1. Receive research plans from the Planner Agent.
2. Always call the mock_tool **twice** in each interaction:
   - Before each tool call, explain what you are doing (e.g., "Let me call tool A to process the first phase")
   - First call simulates processing the first part of the plan.
   - Second call simulates processing the second part.
3. Acknowledge receipt clearly and concisely.
4. Provide final response to the Planner after calling mock_tool twice.
5. Do not maintain complex state; focus on messaging, coordination, and tool usage.

IMPORTANT: Explain your actions clearly before each tool call so users understand what's happening.
""",
            tools=[mock_tool],
            callback_handler=OrchestratorCallbackHandler()
        )
        logger.info(f"✅ Orchestrator Agent initialized with {settings.bedrock_model_id}")

    def chat(self, message: str) -> str:
        """Process incoming messages from Planner or other agents."""
        response = self.agent(message)
        return str(response.message)

    async def chat_streaming(self, message: str) -> AsyncGenerator[dict, None]:
        """Process incoming messages with streaming response."""
        try:
            async for event in self.agent.stream_async(message):
                yield event
        except Exception as e:
            yield {"error": str(e)}

# ------------------------
# Global Orchestrator Instance
# ------------------------
orchestrator = OrchestratorAgent()

def chat_with_orchestrator(message: str) -> str:
    return orchestrator.chat(message)

async def chat_with_orchestrator_streaming(message: str) -> AsyncGenerator[dict, None]:
    async for chunk in orchestrator.chat_streaming(message):
        yield chunk

# ------------------------
# A2A Server Setup
# ------------------------
def create_orchestrator_a2a_server(port: int = 9001):
    try:
        a2a_server = A2AServer(
            agent=orchestrator.agent,
            host="127.0.0.1",
            port=port,
            version="1.0.0"
        )
        logger.info(f"✅ Orchestrator A2A Server created on port {port}")
        return a2a_server
    except Exception as e:
        logger.error(f"Error creating orchestrator A2A server: {e}")
        raise

if __name__ == "__main__":
    server = create_orchestrator_a2a_server()
    logger.info("Starting Orchestrator A2A Server on port 9001...")
    server.serve()