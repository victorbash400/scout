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
# Callback Handler
# ------------------------
class OrchestratorCallbackHandler:
    """Robust callback that sends each tool call and final response to the frontend via main.py webhook."""
    def __init__(self, webhook_url: str = "http://localhost:8000/api/orchestrator/events", min_interval: float = 0.05):
        self.webhook_url = webhook_url
        self.min_interval = min_interval
        self._last_sent_ts = 0.0
        self._last_msg = None

    def _post(self, payload: dict):
        def _do():
            try:
                requests.post(self.webhook_url, json=payload, timeout=5)
            except Exception as e:
                logger.debug(f"Webhook POST failed: {e}")
        threading.Thread(target=_do, daemon=True).start()

    def __call__(self, **kwargs):
        try:
            now = time.time()
            tool_name = kwargs.get("tool_name") or kwargs.get("tool")
            tool_args = kwargs.get("tool_input") or kwargs.get("tool_args")
            message = None
            event_kind = None

            # Detect tool events
            if tool_name:
                message = f"Using {tool_name}..."
                event_kind = "tool"

            # Detect streaming / delta fragments
            elif 'delta' in kwargs or 'text' in kwargs or 'content' in kwargs:
                delta = kwargs.get('delta') or kwargs.get('text') or kwargs.get('content')
                if isinstance(delta, dict):
                    message = delta.get('text') or str(delta)
                else:
                    message = str(delta)
                event_kind = "intermediate"

            # Detect final/completion result messages
            elif 'result' in kwargs or 'message' in kwargs:
                message = kwargs.get('result') or kwargs.get('message')
                event_kind = "final_response"

            else:
                return

            if not message:
                return

            # Throttle duplicates
            if message == self._last_msg and (now - self._last_sent_ts) < self.min_interval:
                return

            payload = {
                "type": "orchestrator_message",
                "event": event_kind,
                "message": str(message),
                "extra": {
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "source_event_type": kwargs.get("event_type")
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            self._post(payload)
            self._last_msg = message
            self._last_sent_ts = now

        except Exception as e:
            logger.error(f"OrchestratorCallbackHandler error: {e}")

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

        # Agent setup
        self.agent = Agent(
            name="SCOUT Orchestrator",
            description="Orchestrator Agent for receiving plans from Planner and coordinating.",
            model=settings.bedrock_model_id,
            system_prompt="""
You are the Orchestrator Agent. Your role:
1. Receive research plans from the Planner Agent.
2. Always call the mock_tool **twice** in each interaction:
   - First call simulates processing the first part of the plan.
   - Second call simulates processing the second part.
3. Acknowledge receipt clearly and concisely.
4. Provide final response to the Planner after calling mock_tool twice.
5. Do not maintain complex state; focus on messaging, coordination, and tool usage.
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
