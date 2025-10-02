import os
import requests
import logging
from typing import List, Dict, AsyncGenerator
from dotenv import load_dotenv
import uuid
import asyncio

from strands import Agent, tool
from config.settings import settings
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

# --- Tool 1: Find Competing Businesses ---
@tool
async def find_competitors(business_type: str, area: str) -> str:
    """
    Finds competing businesses in a specified area using the Google Places API v1.
    It returns a summary of the top 5 competitors found.

    Args:
        business_type: The type of business to search for (e.g., "bakery", "gym").
        area: The geographic location to search within (e.g., "Juja, Kiambu County").

    Returns:
        A string summarizing the number of competitors found and details of the top 5.
    """
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        return "Error: GOOGLE_PLACES_API_KEY is not configured."

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress"
    }
    data = {"textQuery": f"{business_type} in {area}"}

    try:
        # Use aiohttp for async HTTP requests, but since we're using requests,
        # we'll run it in a thread pool to make it non-blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.post(url, headers=headers, json=data))
        response.raise_for_status()
        places_data = response.json()

        competitors = places_data.get("places", [])
        if not competitors:
            return f"No direct competitors found for '{business_type}' in '{area}'."

        summary = f"Found {len(competitors)} direct competitors. Here are the top {min(5, len(competitors))}:\n"
        for i, place in enumerate(competitors[:5]):
            name = place.get('displayName', {}).get('text', 'N/A')
            address = place.get('formattedAddress', 'N/A')
            summary += f"{i+1}. Name: {name}, Address: {address}\n"
        
        return summary.strip()

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed in find_competitors: {e}")
        return f"Error: Failed to communicate with the Google Places API. {e}"

# --- Tool 3: Update Work Progress ---
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
        agentName="CompetitionAgent",
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


# --- Tool 4: Save Competition Report ---
@tool
def save_competition_report(content: str) -> str:
    """
    Saves the competition report to a file and adds the path to the shared storage.
    This ensures the synthesis agent can find the report.
    
    Args:
        content: The competition analysis content to save
    
    Returns:
        A confirmation message
    """
    import os
    
    # Save to the standard report location
    file_path = "reports/competition_report.md"
    
    # Add the file path to the shared storage for the synthesis agent (thread-safe)
    with storage_lock:
        if file_path not in report_filepaths_storage:
            report_filepaths_storage.append(file_path)
            logger.info(f"Competition report path added to storage: {file_path}")
    
    # Use direct file operations instead of strands_tools.file_write
    # since calling another tool directly from within a tool is problematic
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Competition report saved successfully to {file_path}"
    except Exception as e:
        logger.error(f"Failed to save competition report: {e}")
        return f"Error saving competition report: {e}"


# --- CompetitionAgent Class ---
class CompetitionAgent:
    def __init__(self):
        if not os.getenv("GOOGLE_PLACES_API_KEY"):
            raise ValueError("GOOGLE_PLACES_API_KEY environment variable not set.")

        # AWS credentials for Bedrock
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region

        self.agent = Agent(
            name="Competition Agent",
            model=settings.bedrock_model_id,
            system_prompt="""You are a meticulous Competition Analyst. Your mission is to generate a comprehensive, professionally formatted competitive analysis report for a new business in a specific location.

            **Your process must be:**
            1.  **Report STARTED:** Use `update_work_progress` with status 'started' to indicate you've begun the task.
            2.  **Explain your approach:** Briefly explain how you'll analyze the market for competitors.
            3.  **Report IN PROGRESS:** Use `update_work_progress` with status 'in_progress' to indicate you're searching for competitors.
            4.  **Call `find_competitors`:** Use this tool EXACTLY ONCE to get competitor data - make only ONE API call for speed and cost efficiency.
            5.  **Report COMPLETED:** Use `update_work_progress` with status 'completed' to indicate the competitor analysis is done.
            6.  **Save the result:** Use the `save_competition_report` tool to save the competition analysis to a file named `competition_report.md` in the `reports/` directory.

            **REPORT FORMAT:** Create a professional markdown report with:
            - # Main title
            - ## Section headers (Executive Summary, Competitor Analysis, Strategic Recommendations, Sources)
            - Include competitor table with names and addresses from the API data
            - Use bullet points for key insights
            - Include specific data and sources at the bottom (try to use actual links to sources if possible)
            - Keep it focused and actionable
            
            Be conservative with resources - make only ONE data tool call per agent run.
            """,
            tools=[
                find_competitors,
                update_work_progress,
                save_competition_report
            ]
        )
        logger.info("✅ Competition Agent initialized correctly.")

    async def run(self, business_type: str, area: str) -> AsyncGenerator[Dict, None]:
        """
        Runs the agent to generate a full competition analysis and yields the raw stream events.
        The agent will report its progress using the update_work_progress tool.
        """
        prompt = (
            f"Generate a full competition report for a new '{business_type}' in '{area}'. "
            "Follow your instructions precisely to find competitors, "
            "then combine everything into a final summary and save it to a file. "
            "Make only ONE call to find_competitors to be conservative with API usage."
        )
        
        async for event in self.agent.stream_async(prompt):
            yield event

# --- Entry Point for Orchestrator ---

async def run_competition_agent(tasks: List[str]) -> AsyncGenerator[Dict, None]:
    """
    This function is the entry point for the Competition Agent, called by the Orchestrator.
    It expects the 'tasks' list to contain two items: [business_type, area].
    """
    if len(tasks) != 2:
        yield {"error": "The Competition Agent requires exactly two tasks: a business type and an area."}
        return

    business_type, area = tasks
    logger.info(f"🕵️‍♂️ Competition Agent received tasks: Analyze '{business_type}' in '{area}'.")
    
    competition_agent_instance = CompetitionAgent()
    async for event in competition_agent_instance.run(business_type, area):
        # Here, we could add logic to capture the final report if needed
        yield event

# --- Example Usage (for direct testing) ---
async def main():
    test_tasks = ["specialty coffee shop", "Juja, Kiambu County"]
    
    print("\n--- AGENT'S STREAMED EVENTS ---")
    final_report = ""
    async for event in run_competition_agent(test_tasks):
        print(event)
        if event.get('event') == 'contentBlockDelta' and 'text' in event.get('delta', {}):
            final_report += event['delta']['text']
    
    print("\n--- AGENT'S FINAL REPORT ---")
    print(final_report)
    print("----------------------------\n")

if __name__ == "__main__":
    asyncio.run(main())