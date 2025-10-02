import os
import logging
from typing import List, Dict, AsyncGenerator
from dotenv import load_dotenv
import uuid
from datetime import datetime

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


# --- Tool 1: Get Pricing Data ---
@tool
def get_pricing_data(business_type: str, area: str) -> str:
    """
    Fetches real pricing data and competitive pricing analysis using Tavily search API.

    Args:
        business_type: The type of business (e.g., "bakery", "gym")
        area: The geographic area to analyze (e.g., "Nairobi, Kenya")

    Returns:
        Pricing analysis including average prices, competitive pricing, and price positioning recommendations.
    """
    import requests
    import json
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY is not configured."
    
    try:
        # Search for pricing information using Tavily
        search_query = f"{business_type} pricing costs rates {area} market analysis"
        
        url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        data = {
            "api_key": api_key,
            "query": search_query,
            "search_depth": "advanced",
            "include_answer": True,
            "include_raw_content": False,
            "max_results": 5
        }
        
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        search_results = response.json()
        
        # Extract pricing insights from search results
        pricing_insights = []
        if "results" in search_results:
            for result in search_results["results"][:3]:  # Top 3 results
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                pricing_insights.append(f"- **{title}**: {content[:200]}... (Source: {url})")
        
        # Get the AI-generated answer if available
        answer = search_results.get("answer", "No specific pricing data found.")
        
        pricing_info = f"""
Pricing Analysis for {business_type} in {area}:

**Market Research Summary:**
{answer}

**Key Pricing Insights:**
{chr(10).join(pricing_insights)}

**Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}
"""
        return pricing_info
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Tavily API request failed: {e}")
        return f"Error: Failed to fetch pricing data from Tavily API. {e}"
    except Exception as e:
        logger.error(f"Unexpected error in get_pricing_data: {e}")
        return f"Error: Unexpected error occurred while fetching pricing data. {e}"


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
        agentName="PriceAgent",
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


# --- Tool 3: Save Price Report ---
@tool
def save_price_report(content: str) -> str:
    """
    Saves the price report to a file and adds the path to the shared storage.
    This ensures the synthesis agent can find the report.
    
    Args:
        content: The pricing analysis content to save
    
    Returns:
        A confirmation message
    """
    import os
    
    # Save to the standard report location
    file_path = "reports/price_report.md"
    
    # Add the file path to the shared storage for the synthesis agent (thread-safe)
    with storage_lock:
        if file_path not in report_filepaths_storage:
            report_filepaths_storage.append(file_path)
            logger.info(f"Price report path added to storage: {file_path}")
    
    # Use direct file operations instead of strands_tools.file_write
    # since calling another tool directly from within a tool is problematic
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Price report saved successfully to {file_path}"
    except Exception as e:
        logger.error(f"Failed to save price report: {e}")
        return f"Error saving price report: {e}"


# --- PriceAgent Class ---
class PriceAgent:
    def __init__(self):
        # AWS credentials for Bedrock
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region

        self.agent = Agent(
            name="Price Agent",
            model=settings.bedrock_model_id,
            system_prompt="""You are a meticulous Pricing Analyst. Your mission is to generate a comprehensive, professionally formatted pricing analysis report for a new business in a specific location.

            **Your process must be:**
            1.  **Report STARTED:** Use `update_work_progress` with status 'started' to indicate you've begun the task.
            2.  **Explain your approach:** Briefly explain how you'll analyze the pricing for the business.
            3.  **Report IN PROGRESS:** Use `update_work_progress` with status 'in_progress' to indicate you're gathering pricing data.
            4.  **Call `get_pricing_data`:** Use this tool EXACTLY ONCE to get pricing data - make only ONE API call for speed and cost efficiency.
            5.  **Report COMPLETED:** Use `update_work_progress` with status 'completed' to indicate the pricing analysis is done.
            6.  **Save the result:** Use the `save_price_report` tool to save the pricing analysis to a file named `price_report.md` in the `reports/` directory.

            **REPORT FORMAT:** Create a professional markdown report with:
            - # Main title
            - ## Section headers for key areas (Executive Summary, Analysis, Recommendations, Sources)
            - Use bullet points and tables where helpful
            - Include specific data and sources at the bottom (try to use actual links to sources if possible)  
            - Keep it concise but comprehensive
            
            Be conservative with resources - make only ONE data tool call per agent run.
            """,
            tools=[
                get_pricing_data,
                update_work_progress,
                save_price_report
            ]
        )
        logger.info("✅ Price Agent initialized correctly.")

    async def run(self, business_type: str, area: str) -> AsyncGenerator[Dict, None]:
        """
        Runs the agent to generate a full pricing analysis and yields the raw stream events.
        The agent will report its progress using the update_work_progress tool.
        """
        prompt = (
            f"Generate a full pricing analysis report for a new '{business_type}' in '{area}'. "
            "Follow your instructions precisely to gather pricing data and insights, "
            "then combine everything into a final summary and save it to a file. "
            "Make only ONE call to get_pricing_data to be conservative with API usage."
        )
        
        async for event in self.agent.stream_async(prompt):
            yield event


# --- Entry Point for Orchestrator ---

async def run_price_agent(tasks: List[str]) -> AsyncGenerator[Dict, None]:
    """
    This function is the entry point for the Price Agent, called by the Orchestrator.
    It expects the 'tasks' list to contain two items: [business_type, area].
    """
    if len(tasks) != 2:
        yield {"error": "The Price Agent requires exactly two tasks: a business type and an area."}
        return

    business_type, area = tasks
    logger.info(f"💰 Price Agent received tasks: Analyze '{business_type}' in '{area}'.")
    
    price_agent_instance = PriceAgent()
    async for event in price_agent_instance.run(business_type, area):
        yield event