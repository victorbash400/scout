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

# Global storage for report file paths
report_filepaths_storage: List[str] = []

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

@tool
def competition_agent_tool(tasks: List[str]) -> str:
    """Delegates competition-related tasks to the Competition Agent."""
    return run_competition_agent(tasks)

@tool
def market_agent_tool(tasks: List[str]) -> str:
    """Delegates market-related tasks to the Market Agent."""
    return run_market_agent(tasks)

@tool
def price_agent_tool(tasks: List[str]) -> str:
    """Delegates price-related tasks to the Price Agent."""
    return run_price_agent(tasks)

@tool
def legal_agent_tool(tasks: List[str]) -> str:
    """Delegates legal-related tasks to the Legal Agent."""
    return run_legal_agent(tasks)

@tool
def execute_research_plan() -> str:
    """
    Executes the research plan by calling the specialist agents directly.
    This should be called after the user has approved the plan.
    """
    global todo_list_storage, report_filepaths_storage
    logger.info("Executing research plan...")
    
    filepaths = []
    if todo_list_storage["competition_tasks"]:
        filepaths.append(run_competition_agent(todo_list_storage["competition_tasks"]))
    if todo_list_storage["market_tasks"]:
        filepaths.append(run_market_agent(todo_list_storage["market_tasks"]))
    if todo_list_storage["price_tasks"]:
        filepaths.append(run_price_agent(todo_list_storage["price_tasks"]))
    if todo_list_storage["legal_tasks"]:
        filepaths.append(run_legal_agent(todo_list_storage["legal_tasks"]))
        
    report_filepaths_storage.extend(filepaths)
    return f"Research finished. Reports generated at: {filepaths}"

@tool
def run_synthesis_agent_tool() -> str:
    """Calls the Synthesis Agent to compile the final report."""
    global report_filepaths_storage
    return run_synthesis_agent(report_filepaths_storage)

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
            2. For each research category, first explain to the user why you are adding tasks for that category, and then use the `update_todo_list` tool to add the tasks. You must follow this explain-then-call pattern for each category.
            3. After creating the plan, ask the user for confirmation to proceed.
            4. Once the user confirms, your first action is to call the appropriate specialist agent tools (`competition_agent_tool`, `market_agent_tool`, etc.) to execute the research plan.
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
                run_synthesis_agent_tool,
                competition_agent_tool,
                market_agent_tool,
                price_agent_tool,
                legal_agent_tool
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

def get_planner_todo_list():
    """Get the current to-do list from the planner agent."""
    return todo_list_storage.copy()

def clear_report_filepaths():
    """Clears the report filepaths storage."""
    global report_filepaths_storage
    report_filepaths_storage = []

def clear_planner_todo_list():
    """Clear the to-do list from the planner agent."""
    global todo_list_storage
    todo_list_storage = {
        "competition_tasks": [],
        "market_tasks": [],
        "financial_tasks": [],
        "risk_tasks": [],
        "synthesis_requirements": []
    }
    clear_report_filepaths()

def chat_with_planner(message: str) -> str:
    return planner.chat(message)

async def chat_with_planner_streaming(message: str) -> AsyncGenerator[str, None]:
    async for chunk in planner.chat_streaming(message):
        yield chunk