import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

from strands import Agent
from config.settings import settings
from strands import Agent, tool

class LegalAgent:
    def __init__(self):
        self.agent = Agent(
            name="Legal Agent",
            model=settings.bedrock_model_id,
            system_prompt="""You are the Legal Agent. When you receive a list of tasks, your only job is to respond with a confirmation message stating that you have received the tasks and are ready. For example: 'The Legal Agent is on standby and has received its tasks.'""",
            tools=[]
        )

    def run(self, tasks: List[str]) -> str:
        """Runs the agent to confirm receipt of tasks."""
        task_str = ", ".join(tasks)
        response = self.agent(f"I have been assigned the following tasks: {task_str}")
        return str(response.message)

# Create a global instance of the agent
legal_agent = LegalAgent()

def run_legal_agent(tasks: List[str]) -> str:
    """
    This function is the entry point for the Legal Agent.
    It calls the run method on the global agent instance.
    """
    return legal_agent.run(tasks)