
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


# --- Tool 1: Get Legal Requirements ---
@tool
def get_legal_requirements(business_type: str, area: str) -> str:
    """
    Fetches real legal requirements and compliance data using Tavily search API.

    Args:
        business_type: The type of business (e.g., "bakery", "gym")
        area: The geographic area to analyze (e.g., "Nairobi, Kenya")

    Returns:
        Legal compliance requirements including licenses, permits, and regulations.
    """
    import requests
    import json
    from datetime import datetime
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY is not configured."
    
    try:
        # Search for legal requirements using Tavily
        search_query = f"{business_type} business license permits legal requirements {area} regulations compliance"
        
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
        
        # Extract legal insights from search results
        legal_insights = []
        if "results" in search_results:
            for result in search_results["results"][:3]:  # Top 3 results
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                legal_insights.append(f"- **{title}**: {content[:200]}... (Source: {url})")
        
        # Get the AI-generated answer if available
        answer = search_results.get("answer", "No specific legal requirements found.")
        
        legal_info = f"""
Legal Requirements for {business_type} in {area}:

**Legal Research Summary:**
{answer}

**Key Legal Requirements:**
{chr(10).join(legal_insights)}

**Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}
"""
        return legal_info
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Tavily API request failed: {e}")
        return f"Error: Failed to fetch legal data from Tavily API. {e}"
    except Exception as e:
        logger.error(f"Unexpected error in get_legal_requirements: {e}")
        return f"Error: Unexpected error occurred while fetching legal data. {e}"


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
        agentName="LegalAgent",
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


# --- Tool 3: Save Legal Report ---
@tool
def save_legal_report(content: str) -> str:
    """
    Saves the legal report to a file and adds the path to the shared storage.
    This ensures the synthesis agent can find the report.
    
    Args:
        content: The legal analysis content to save
    
    Returns:
        A confirmation message
    """
    import os
    
    # Save to the standard report location
    file_path = "reports/legal_report.md"
    
    # Add the file path to the shared storage for the synthesis agent (thread-safe)
    with storage_lock:
        if file_path not in report_filepaths_storage:
            report_filepaths_storage.append(file_path)
            logger.info(f"Legal report path added to storage: {file_path}")
    
    # Use direct file operations instead of strands_tools.file_write
    # since calling another tool directly from within a tool is problematic
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Legal report saved successfully to {file_path}"
    except Exception as e:
        logger.error(f"Failed to save legal report: {e}")
        return f"Error saving legal report: {e}"


class LegalAgent:
    def __init__(self):
        # AWS credentials for Bedrock
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region

        self.agent = Agent(
            name="Legal Agent",
            model=settings.bedrock_model_id,
            system_prompt="""You are the Legal Compliance Specialist. Your mission is to generate a comprehensive, professionally formatted legal compliance report for a new business in a specific location.

            **Your process must be:**
            1.  **Report STARTED:** Use `update_work_progress` with status 'started' to indicate you've begun the task.
            2.  **Explain your approach:** Briefly explain how you'll analyze the legal requirements for the business.
            3.  **Report IN PROGRESS:** Use `update_work_progress` with status 'in_progress' to indicate you're gathering legal compliance data.
            4.  **Call `get_legal_requirements`:** Use this tool EXACTLY ONCE to get legal requirements - make only ONE API call for speed and cost efficiency.
            5.  **Report COMPLETED:** Use `update_work_progress` with status 'completed' to indicate the legal analysis is done.
            6.  **Save the result:** Use the `save_legal_report` tool to save the legal compliance analysis to a file named `legal_report.md` in the `reports/` directory.

            **REPORT FORMAT:** Create a professional markdown report with:
            - # Main title
            - ## Section headers (Executive Summary, Key Requirements, Compliance Steps, Costs, Sources)
            - Use bullet points and simple tables for licenses/permits
            - Include specific legal requirements from research
            - Include sources and legal disclaimer at the bottom (try to use actual links to sources if possible)
            - Keep it practical and actionable
            
            Be conservative with resources - make only ONE data tool call per agent run.
            """,
            tools=[
                get_legal_requirements,
                update_work_progress,
                save_legal_report
            ]
        )
        logger.info("✅ Legal Agent initialized successfully.")

    async def run(self, business_type: str, area: str) -> AsyncGenerator[Dict, None]:
        """Runs the agent and yields the raw stream events."""
        prompt = (
            f"Generate a legal compliance report for a new '{business_type}' in '{area}'. "
            "Follow your instructions precisely to gather legal requirements and compliance data, "
            "then combine everything into a final summary and save it to a file. "
            "Make only ONE call to get_legal_requirements to be conservative with API usage."
        )
        
        async for event in self.agent.stream_async(prompt):
            yield event

# --- Entry Point for Orchestrator ---

async def run_legal_agent(tasks: List[str]) -> AsyncGenerator[Dict, None]:
    """
    This function is the entry point for the Legal Agent, called by the Orchestrator.
    It expects the 'tasks' list to contain two items: [business_type, area].
    """
    if len(tasks) != 2:
        yield {"error": "The Legal Agent requires exactly two tasks: a business type and an area."}
        return

    business_type, area = tasks
    logger.info(f"⚖️ Legal Agent received tasks: Analyze '{business_type}' in '{area}'.")
    
    legal_agent_instance = LegalAgent()
    async for event in legal_agent_instance.run(business_type, area):
        yield event
