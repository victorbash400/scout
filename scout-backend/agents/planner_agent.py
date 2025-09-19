import os
import asyncio
from typing import AsyncGenerator
from strands import Agent
from dotenv import load_dotenv
from config.settings import settings

load_dotenv()

class PlannerAgent:
    def __init__(self):
        os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        os.environ['AWS_DEFAULT_REGION'] = settings.aws_region
        print("✅ AWS credentials loaded successfully")

        self.agent = Agent(
            model=settings.bedrock_model_id,
            system_prompt="""You are SCOUT, a concise business planning assistant. Keep answers short and helpful."""
        )
        self.session_memory = []  # In-session memory for chat history
        print(f"✅ Planner Agent initialized with {settings.bedrock_model_id}")

    def chat(self, message: str) -> str:
        self.session_memory.append({"role": "user", "content": message})
        response = self.agent(message)
        self.session_memory.append({"role": "assistant", "content": str(response.message)})
        return str(response.message)

    async def chat_streaming(self, message: str) -> AsyncGenerator[dict, None]:
        self.session_memory.append({"role": "user", "content": message})
        full_response = []
        try:
            async for event in self.agent.stream_async(message):
                yield event
                if event.get('type') == 'content_delta':
                    full_response.append(event['delta']['text'])
            self.session_memory.append({"role": "assistant", "content": "".join(full_response)})
        except Exception as e:
            yield {"error": str(e)}

planner = PlannerAgent()

def chat_with_planner(message: str) -> str:
    return planner.chat(message)

async def chat_with_planner_streaming(message: str) -> AsyncGenerator[str, None]:
    async for chunk in planner.chat_streaming(message):
        yield chunk
