import os
import logging
from typing import List, Dict, AsyncGenerator
from dotenv import load_dotenv
import uuid

from strands import Agent, tool
from config.settings import settings
from utils.event_queue import event_queue, StreamEvent

# Import the global storage from shared module
from agents.shared_storage import report_filepaths_storage, storage_lock

# Load environment variables from .env file
load_dotenv()

# Bypass tool consent for automated file operations
os.environ["BYPASS_TOOL_CONSENT"] = "true"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Tool 1: Get Market Data ---
@tool
def get_market_data(business_type: str, area: str) -> str:
    """
    Fetches market data for a specified business type in a specific area.

    Args:
        business_type: The type of business (e.g., "bakery", "gym")
        area: The geographic area to analyze (e.g., "Nairobi, Kenya")

    Returns:
        Market data analysis including size, trends, and growth potential.
    """
    # Simulated market data - in a real implementation, this would call actual APIs
    market_info = f"""
    Market Analysis for {business_type} in {area}:
    
    - Market Size: Medium
    - Growth Potential: High
    - Key Trends: Consumer preference for local products, premium offerings
    - Customer Demographics: Age 25-45, Middle to upper income
    - Seasonal Variations: Higher demand during holidays and weekends
    - Average Price Points: Mid-range to premium
    """
    return market_info


# --- Tool 2: Update Work Progress ---
@tool
async def update_work_progress(status: str, message: str, task: str) -> str:
    """
    Updates the work progress for the specialist agent monitor.
    This tool is called by the agent to report its current status.
    
    Args:
        status: Current status ('started', 'in_progress', 'completed', 'error')
        message: Detailed message about what's happening
        task: The specific task being worked on
    
    Returns:
        A confirmation message
    """
    # Create a StreamEvent and put it in the event queue
    event = StreamEvent(
        agentName="MarketAgent",
        eventType="tool_call",
        payload={
            "tool_name": "update_work_progress",
            "tool_input": {"status": status, "message": message, "task": task},
            "display_message": f"{message}"
        },
        traceId=str(uuid.uuid4()),
        spanId=str(uuid.uuid4()),
        parentSpanId="planner"
    )
    
    try:
        event_queue.get_queue().put_nowait(event.dict())
        logger.info(f"Work progress update sent: {status} - {message}")
    except Exception as e:
        logger.error(f"Failed to send work progress update: {e}")
    
    return f"Work progress updated: {status} - {task}"


# --- Tool 3: Save Market Report ---
@tool
def save_market_report(content: str) -> str:
    """
    Saves the market report to a file and adds the path to the shared storage.
    This ensures the synthesis agent can find the report.
    
    Args:
        content: The market analysis content to save
    
    Returns:
        A confirmation message
    """
    import os
    
    # Save to the standard report location
    file_path = "reports/market_report.md"
    
    # Add the file path to the shared storage for the synthesis agent (thread-safe)
    with storage_lock:
        if file_path not in report_filepaths_storage:
            report_filepaths_storage.append(file_path)
            logger.info(f"Market report path added to storage: {file_path}")
    
    # Use direct file operations instead of strands_tools.file_write
    # since calling another tool directly from within a tool is problematic
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Market report saved successfully to {file_path}"
    except Exception as e:
        logger.error(f"Failed to save market report: {e}")
        return f"Error saving market report: {e}"


# --- MarketAgent Class ---
class MarketAgent:
    def __init__(self):
        # AWS credentials for Bedrock
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region

        self.agent = Agent(
            name="Market Agent",
            model=settings.bedrock_model_id,
            system_prompt="""You are a meticulous Market Analyst. Your mission is to generate a market analysis report for a new business in a specific location. You must use the provided tools in a logical sequence and report your progress using the update_work_progress tool.

            **Your process must be:**
            1.  **Report STARTED:** Use `update_work_progress` with status 'started' to indicate you've begun the task.
            2.  **Explain your approach:** Briefly explain how you'll analyze the market for the business.
            3.  **Report IN PROGRESS:** Use `update_work_progress` with status 'in_progress' to indicate you're gathering market data.
            4.  **Call `get_market_data`:** Use this tool ONCE to get market data for the specified business type in the area - make only ONE search and be conservative with API usage.
            5.  **Report COMPLETED:** Use `update_work_progress` with status 'completed' to indicate the market analysis is done.
            6.  **Save the result:** Use the `save_market_report` tool to save the market analysis to a file named `market_report.md` in the `reports/` directory.
            
            Remember to be conservative with resources - only use the get_market_data and save_market_report tools.
            Be very explicit about using the update_work_progress tool at each major step to report status to the monitor.
            """,
            tools=[
                get_market_data,
                update_work_progress,
                save_market_report
            ]
        )
        logger.info("✅ Market Agent initialized correctly.")

    async def run(self, business_type: str, area: str) -> AsyncGenerator[Dict, None]:
        """
        Runs the agent to generate a full market analysis and yields the raw stream events.
        The agent will report its progress using the update_work_progress tool.
        """
        prompt = (
            f"Generate a full market analysis report for a new '{business_type}' in '{area}'. "
            "Follow your instructions precisely to gather market data and location insights, "
            "then combine everything into a final summary and save it to a file. "
            "Make only ONE call to get_market_data to be conservative with API usage."
        )
        
        async for event in self.agent.stream_async(prompt):
            yield event


# --- Entry Point for Orchestrator ---

async def run_market_agent(tasks: List[str]) -> AsyncGenerator[Dict, None]:
    """
    This function is the entry point for the Market Agent, called by the Orchestrator.
    It expects the 'tasks' list to contain two items: [business_type, area].
    """
    if len(tasks) != 2:
        yield {"error": "The Market Agent requires exactly two tasks: a business type and an area."}
        return

    business_type, area = tasks
    logger.info(f"📊 Market Agent received tasks: Analyze '{business_type}' in '{area}'.")
    
    market_agent_instance = MarketAgent()
    async for event in market_agent_instance.run(business_type, area):
        yield event