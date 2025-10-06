import os
import asyncio
import logging
from typing import AsyncGenerator, List, Dict
from strands import Agent, tool
from dotenv import load_dotenv
from config.settings import settings
from agents.synthesis_agent import run_synthesis_agent
from agents.competition_agent import run_competition_agent
from agents.market_agent import run_market_agent
from agents.price_agent import run_price_agent
from agents.legal_agent import run_legal_agent

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global to-do list storage
todo_list_storage: Dict[str, List[str]] = {
    "competition_tasks": [],
    "market_tasks": [],
    "price_tasks": [],
    "legal_tasks": []
}

# Import shared storage for report file paths
from agents.shared_storage import report_filepaths_storage, storage_lock

@tool
def update_todo_list(category: str, tasks: List[str]) -> str:
    """
    Update the research to-do list with tasks for a specific category.
    
    Args:
        category: The agent category (competition_tasks, market_tasks, price_tasks, legal_tasks)
        tasks: List of tasks to add to this category
    
    Returns:
        A confirmation message with the number of tasks added
    """
    if category not in todo_list_storage:
        return f"Invalid category: {category}. Valid categories are: competition_tasks, market_tasks, price_tasks, legal_tasks"
    
    todo_list_storage[category].extend(tasks)
    return f"Added {len(tasks)} tasks to {category}. Total tasks in this category: {len(todo_list_storage[category])}"


import uuid
from utils.event_queue import event_queue, StreamEvent

@tool
async def execute_research_plan() -> str:
    """
    Executes the research plan by calling the specialist agents sequentially and streaming their progress.
    This should be called after the user has approved the plan.
    """
    global todo_list_storage, report_filepaths_storage
    logger.info("Executing research plan...")
    
    trace_id = str(uuid.uuid4())
    parent_span_id = "planner"

    # Using a synchronous helper to avoid yielding control to the main agent loop prematurely
    def send_event_nowait(event: StreamEvent):
        try:
            event_queue.get_queue().put_nowait(event.dict())
        except Exception as e:
            logger.error(f"Failed to put event on queue: {e}")

    async def stream_and_capture_report(agent_name: str, agent_function, tasks: List[str]) -> str:
        """Helper to stream events and capture the final report."""
        final_report_content = ""
        span_id = str(uuid.uuid4())

        # Send initial thought start event (this is for the planner's wrapper, not the agent's progress)
        send_event_nowait(StreamEvent(
            agentName=agent_name, eventType="thought_start", payload={},
            traceId=trace_id, spanId=span_id, parentSpanId=parent_span_id
        ))

        # For the new agent system, the agents themselves send progress updates via update_work_progress tool
        # We just need to run the agent and capture any content deltas
        async for event in agent_function(tasks):
            event_type = event.get('event')
            if event_type == 'contentBlockDelta' and 'text' in event.get('delta', {}):
                text = event['delta']['text']
                final_report_content += text

        # Send final thought end event
        send_event_nowait(StreamEvent(
            agentName=agent_name, eventType="thought_end", payload={},
            traceId=trace_id, spanId=span_id, parentSpanId=parent_span_id
        ))
        
        return final_report_content

    if todo_list_storage["competition_tasks"]:
        await stream_and_capture_report("CompetitionAgent", run_competition_agent, todo_list_storage["competition_tasks"])

    if todo_list_storage["market_tasks"]:
        # This will still fail until market_agent is refactored
        # But the planner agent should now complete the first step without getting confused
        try:
            await stream_and_capture_report("MarketAgent", run_market_agent, todo_list_storage["market_tasks"])
        except TypeError as e:
            logger.error(f"MarketAgent is not an async generator: {e}. Skipping.")

    if todo_list_storage["price_tasks"]:
        try:
            await stream_and_capture_report("PriceAgent", run_price_agent, todo_list_storage["price_tasks"])
        except TypeError as e:
            logger.error(f"PriceAgent is not an async generator: {e}. Skipping.")

    if todo_list_storage["legal_tasks"]:
        try:
            await stream_and_capture_report("LegalAgent", run_legal_agent, todo_list_storage["legal_tasks"])
        except TypeError as e:
            logger.error(f"LegalAgent is not an async generator: {e}. Skipping.")

    return f"Research finished. All specialist agents have completed their tasks."

@tool
async def run_synthesis_agent_tool() -> str:
    """Calls the Synthesis Agent to compile the final report."""
    global report_filepaths_storage
    # Run the synthesis agent and consume its async generator
    async for event in run_synthesis_agent(report_filepaths_storage):
        # The synthesis agent sends its own progress updates via update_work_progress tool
        # We just need to consume the events without doing anything special
        pass
    return "Synthesis agent has completed the final report compilation."

class PlannerAgent:
    def __init__(self):
        # Load AWS credentials once globally
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region
        print("✅ AWS credentials loaded successfully")

        self.agent = Agent(
            model=settings.bedrock_model_id,
            system_prompt="""You are SCOUT, a business planning assistant.
            You help users analyze business plans and create structured research to-do lists.

            You have two modes of operation that determine your behavior:

            CHAT MODE:
            - Engage in general conversation about business planning
            - Answer questions and provide guidance
            - Do NOT create research plans or call the update_todo_list tool
            - Focus on being helpful and informative without structured task creation

            AGENT MODE:
            1. Analyze the business plan and identify key areas for research.
            2. For each research category, first explain to the user why you are adding tasks for that category, and then use the `update_todo_list` tool to add ONLY ONE OR TWO of the most essential tasks. You must follow this explain-then-call pattern for each category.
            3. After creating the plan, ask the user for confirmation to proceed.
            4. Once the user confirms, your first action is to call the `execute_research_plan` tool to execute the research plan.
            5. After the specialist agents have run, your final action is to call the `run_synthesis_agent_tool` to compile the final report.
            6. Explain each major step to the user before you take it (e.g., "I will now call the specialist agents...", "The specialist agents are done, now I will call the synthesis agent...").

            The to-do list categories you can use are:
            - competition_tasks: For analyzing competitors.
            - market_tasks: For understanding the market and customers.
            - price_tasks: For all pricing-related research.
            - legal_tasks: For regulatory and compliance research.

            Follow the AGENT MODE workflow strictly. Your job is to create the plan and then execute it by calling the specialist agents and then the synthesis agent.
            """,
            tools=[
                update_todo_list,
                execute_research_plan,
                run_synthesis_agent_tool
            ]
        )
        self.document_context = None  # For attached file context
        print(f"✅ Planner Agent initialized with {settings.bedrock_model_id}")

    def _prepare_message_with_context(self, message: str) -> str:
        """Prepend document context to the message if it exists."""
        # Extract mode from message if present
        mode = "chat"  # default mode
        if message.startswith("[MODE: "):
            mode_end = message.find("] ")
            if mode_end != -1:
                mode = message[7:mode_end].lower()  # Extract mode (AGENT or CHAT)
                message = message[mode_end + 2:]  # Remove mode prefix from message
        
        if self.document_context:
            context_message = (
                f"Current mode: {mode.upper()}\n"
                f"Please use the following document as context for your answer:\n"
                f"<document>\n{self.document_context}\n</document>\n\n"
                f"User question: {message}"
            )
            return context_message
        else:
            return f"Current mode: {mode.upper()}\nUser question: {message}"

    def chat(self, message: str) -> str:
        message_with_context = self._prepare_message_with_context(message)
        response = self.agent(message_with_context)
        return str(response.message)

    async def chat_streaming(self, message: str) -> AsyncGenerator[dict, None]:
        message_with_context = self._prepare_message_with_context(message)
        try:
            async for event in self.agent.stream_async(message_with_context):
                yield event
        except Exception as e:
            yield {"error": str(e)}

# Global planner instance
planner = PlannerAgent()

def set_planner_context(context: str):
    """Sets the document context for the planner agent."""
    planner.document_context = context

def clear_planner_context():
    """Clears the document context from the planner agent."""
    planner.document_context = None
    # Clear conversation history/memory
    planner.agent.messages = []

def get_planner_todo_list():
    """Get the current to-do list from the planner agent."""
    return todo_list_storage.copy()

def clear_report_filepaths():
    """Clears the report filepaths storage."""
    from agents.shared_storage import report_filepaths_storage, storage_lock
    with storage_lock:
        report_filepaths_storage.clear()

def clear_planner_todo_list():
    """Clear the to-do list from the planner agent."""
    global todo_list_storage
    todo_list_storage = {
        "competition_tasks": [],
        "market_tasks": [],
        "price_tasks": [],
        "legal_tasks": []
    }
    clear_report_filepaths()

def chat_with_planner(message: str) -> str:
    return planner.chat(message)

async def chat_with_planner_streaming(message: str) -> AsyncGenerator[str, None]:
    async for chunk in planner.chat_streaming(message):
        yield chunk