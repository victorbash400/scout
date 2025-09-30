
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


# --- Tool: Update Work Progress ---
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
            system_prompt="""You are the Legal Agent. Your mission is to generate a legal compliance report for a new business. You must use the provided tools in a logical sequence and report your progress using the update_work_progress tool.

            **Your process must be:**
            1.  **Report STARTED:** Use `update_work_progress` with status 'started' to indicate you've begun the task.
            2.  **Explain your approach:** Briefly explain how you'll analyze the legal requirements for the business.
            3.  **Report IN PROGRESS:** Use `update_work_progress` with status 'in_progress' to indicate you're gathering legal compliance data.
            4.  **Report COMPLETED:** Use `update_work_progress` with status 'completed' to indicate the legal analysis is done.
            5.  **Save the result:** Use the `save_legal_report` tool to save the legal compliance analysis to a file named `legal_report.md` in the `reports/` directory.
            
            Remember to be conservative with resources - only use the update_work_progress and save_legal_report tools.
            Be very explicit about using the update_work_progress tool at each major step to report status to the monitor.
            """,
            tools=[
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
            "then save the final report to a file."
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
