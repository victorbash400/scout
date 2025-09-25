import os
from dotenv import load_dotenv

load_dotenv()

from strands import Agent
from config.settings import settings
from strands import Agent, tool

class SynthesisAgent:
    def __init__(self):
        self.agent = Agent(
            name="Synthesis Agent",
            model=settings.bedrock_model_id,
            system_prompt="""You are the Synthesis Agent. When called, your only job is to respond with a confirmation message that you are ready to begin synthesis. For example: 'The Synthesis Agent is ready to compile the final report.'""",
            tools=[]
        )

    def run(self) -> str:
        """Runs the agent to confirm it's ready."""
        response = self.agent("I am being called to synthesize the research findings.")
        return str(response.message)

# Create a global instance of the agent
synthesis_agent = SynthesisAgent()

def run_synthesis_agent() -> str:
    """
    This function is the entry point for the Synthesis Agent.
    It calls the run method on the global agent instance.
    """
    return synthesis_agent.run()