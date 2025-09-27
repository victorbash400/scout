import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

from strands import Agent
from config.settings import settings
from strands import Agent, tool
from strands_tools import file_write

class LegalAgent:
    def __init__(self):
        # Load AWS credentials (optional, but needed for Bedrock)
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region

        self.agent = Agent(
            name="Legal Agent",
            model=settings.bedrock_model_id,
            system_prompt="""You are the Legal Agent. When you receive a list of tasks, your only job is to respond with a confirmation message stating that you have received the tasks and are ready. For example: 'The Legal Agent is on standby and has received its tasks.' Then, save this confirmation message to a file named `legal_report.md` in the `reports/` directory.""",
            tools=[file_write]
        )

    def run(self, tasks: List[str]) -> str:
        """Runs the agent to confirm receipt of tasks."""
        task_str = ", ".join(tasks)
        prompt = f"I have been assigned the following tasks: {task_str}. Save the confirmation message to a file."
        response = self.agent(prompt)
        return str(response.message)

# Create a global instance of the agent
legal_agent = LegalAgent()

def run_legal_agent(tasks: List[str]) -> str:
    """
    This function is the entry point for the Legal Agent.
    It calls the run method on the global agent instance.
    """
    return legal_agent.run(tasks)