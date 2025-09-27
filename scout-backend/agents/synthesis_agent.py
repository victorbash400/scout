import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

from strands import Agent
from config.settings import settings
from strands_tools import file_read, file_write

class SynthesisAgent:
    def __init__(self):
        # Load AWS credentials (optional, but needed for Bedrock)
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region

        self.agent = Agent(
            name="Synthesis Agent",
            model=settings.bedrock_model_id,
            system_prompt="""You are the Synthesis Agent. Your mission is to compile a final, comprehensive business report from the findings of other agents.

            **Your process must be:**
            1.  You will be given a list of file paths pointing to the reports from the specialist agents.
            2.  **Read the reports:** For each file path in the list, you must call the `file_read` tool to get the content of that specific file.
            3.  **Synthesize the content:** After reading all the files, analyze the combined information and create a single, cohesive, and well-structured final report in Markdown format. The report should have a clear title, an executive summary, and sections for each of the original analysis areas (Competition, Market, Pricing, Legal).
            4.  **Save the final report:** Use the `file_write` tool to save the complete report to a file named `final_report.md` in the `reports/` directory.
            5.  **Confirm completion:** Your final output should be a confirmation message stating that the synthesis is complete and the file has been saved.
            """,
            tools=[file_read, file_write]
        )

    def run(self, filepaths: List[str]) -> str:
        """Runs the agent to synthesize the reports from the given file paths."""
        prompt = f"The reports from the specialist agents are located at the following paths: {filepaths}. Please read each one, synthesize them into a final report, and save it."
        response = self.agent(prompt)
        return str(response.message)

# Create a global instance of the agent
synthesis_agent = SynthesisAgent()

def run_synthesis_agent(filepaths: List[str]) -> str:
    """
    This function is the entry point for the Synthesis Agent.
    It calls the run method on the global agent instance.
    """
    return synthesis_agent.run(filepaths)