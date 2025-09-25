import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

from strands import Agent
from config.settings import settings
from strands import Agent, tool

class PriceAgent:
    def __init__(self):
        self.agent = Agent(
            name="Price Agent",
            model=settings.bedrock_model_id,
            system_prompt="""You are the Price Agent. When you receive a list of tasks, your only job is to respond with a confirmation message stating that you have received the tasks and are ready. For example: 'The Price Agent is on standby and has received its tasks.'""",
            tools=[]
        )

    def run(self, tasks: List[str]) -> str:
        """Runs the agent to confirm receipt of tasks."""
        task_str = ", ".join(tasks)
        response = self.agent(f"I have been assigned the following tasks: {task_str}")
        return str(response.message)

# Create a global instance of the agent
price_agent = PriceAgent()

def run_price_agent(tasks: List[str]) -> str:
    """
    This function is the entry point for the Price Agent.
    It calls the run method on the global agent instance.
    """
    return price_agent.run(tasks)