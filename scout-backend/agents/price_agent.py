import os
from typing import List
from dotenv import load_dotenv
from config.settings import settings

load_dotenv()

from strands import Agent
from strands_tools.tavily import tavily_search
from strands_tools import file_write

class PriceAgent:
    def __init__(self):
        # Load AWS credentials (optional, but needed for Bedrock)
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region

        self.agent = Agent(
            name="Price Agent",
            model=settings.bedrock_model_id,
            system_prompt="""
You are a meticulous Pricing Strategy Analyst. Your mission is to generate a pricing strategy report for a business in a specific location. You must use the provided tools in a logical sequence.

**Your process must be:**
1. **State your plan.** First, analyze the user's request and state that you will begin by searching for competitor prices and local market conditions.
2. **Call `tavily_search`:** Use this tool to get competitor pricing and market data for the specified business type, products, and location.
3. **State the next step.** After getting the search results, explain how you will use this information to recommend a pricing strategy.
4. **Synthesize the Final Recommendation:** Combine the information from the tool into a single, comprehensive final answer. The report should include a summary of competitor prices, your recommended pricing strategy (e.g., competitive, premium, penetration), and clear reasoning. Always cite sources when possible.
5.  **Save the report:** Use the `file_write` tool to save the final report to a file named `price_report.md` in the `reports/` directory.
            """,
            tools=[tavily_search, file_write]
        )

    def run(self, tasks: List[str]) -> str:
        """Runs the agent with the given tasks, letting the system prompt control the process."""
        task_str = ", ".join(tasks)
        prompt = f"{task_str}. Save the final report to a file."
        response = self.agent(prompt)
        return str(response.message)

# Create a global instance of the agent
price_agent = PriceAgent()

def run_price_agent(tasks: List[str]) -> str:
    """
    This function is the entry point for the Price Agent.
    It calls the run method on the global agent instance.
    """
    return price_agent.run(tasks)