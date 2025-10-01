import os
import logging
import uuid
from typing import List, Dict, AsyncGenerator
from dotenv import load_dotenv

from strands import Agent, tool
from config.settings import settings
from utils.event_queue import event_queue, StreamEvent
from agents.shared_storage import report_filepaths_storage, storage_lock
from strands_tools import file_read

# Load environment variables
load_dotenv()
os.environ["BYPASS_TOOL_CONSENT"] = "true"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Tool 1: Update Work Progress ---
@tool
async def update_work_progress(status: str, message: str, task: str) -> str:
    """
    Updates the work progress for the specialist agent monitor.
    This tool is called by the agent to report its current status.
    """
    event = StreamEvent(
        agentName="SynthesisAgent",
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
    except Exception as e:
        pass  # Only log errors if needed
    return f"Work progress updated: {status} - {task}"

# --- Tool 2: Save Final Report ---
@tool
def save_final_report(content: str) -> str:
    """
    Saves the final synthesized report to a file and adds the path to shared storage.
    """
    file_path = "reports/final_report.md"
    with storage_lock:
        if file_path not in report_filepaths_storage:
            report_filepaths_storage.append(file_path)
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        # Send a final update to the frontend
        event = StreamEvent(
            agentName="SynthesisAgent",
            eventType="tool_call",
            payload={
                "tool_name": "save_final_report",
                "tool_input": {"file_path": file_path},
                "display_message": "Final report generated and saved."
            },
            traceId=str(uuid.uuid4()),
            spanId=str(uuid.uuid4()),
            parentSpanId="planner"
        )
        event_queue.get_queue().put_nowait(event.dict())
        return f"Final report saved successfully to {file_path}"
    except Exception:
        return f"Error saving final report."

# --- Tool 3: Combine Reports ---
@tool
def combine_reports(filepaths: list, output_path: str = "reports/final_report.md") -> str:
    """
    Combines the contents of the given report files into a single Markdown file.
    """
    combined_content = ""
    for path in filepaths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                combined_content += f"\n\n---\n\n" + f.read()
        else:
            combined_content += f"\n\n---\n\n# Missing file: {path}\n"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with storage_lock:
        with open(output_path, 'w', encoding='utf-8') as out:
            out.write(combined_content)
        if output_path not in report_filepaths_storage:
            report_filepaths_storage.append(output_path)
    return output_path

# --- SynthesisAgent Class ---
class SynthesisAgent:
    def __init__(self):
        # Ensure AWS credentials are set for Bedrock
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region
        self.agent = Agent(
            name="Synthesis Agent",
            model=settings.bedrock_model_id,  # Use LLM as in other agents
            system_prompt="""
You are the Synthesis Agent. Your job is to:
1. Send a progress update ('started') when you receive the task.
2. Combine the provided report files using the combine_reports tool.
3. Send a progress update ('completed') when the final report is created.
""",
            tools=[combine_reports, update_work_progress]
        )
        logger.info("✅ Synthesis Agent initialized.")

    async def run(self, filepaths: list):
        prompt = f"Received synthesis task. Please combine the following reports: {filepaths} and save the result as final_report.md. Send a progress update when you start and when you finish."
        async for event in self.agent.stream_async(prompt):
            yield event

# --- Entry Point for Orchestrator ---
async def run_synthesis_agent(filepaths: list):
    agent = SynthesisAgent()
    async for event in agent.run(filepaths):
        yield event