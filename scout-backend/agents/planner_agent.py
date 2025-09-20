import os
import asyncio
from typing import AsyncGenerator, List, Dict
from strands import Agent, tool
from dotenv import load_dotenv
from config.settings import settings
from .orchestrator_tool import orchestrator_tool
from .specialist_tools import synthesis_agent_tool

load_dotenv()

# Global to-do list storage
todo_list_storage: Dict[str, List[str]] = {
    "competition_tasks": [],
    "market_tasks": [],
    "financial_tasks": [],
    "risk_tasks": [],
    "synthesis_requirements": []
}

@tool
def update_todo_list(category: str, tasks: List[str]) -> str:
    """
    Update the research to-do list with tasks for a specific category.
    
    Args:
        category: The agent category (competition_tasks, market_tasks, financial_tasks, risk_tasks, synthesis_requirements)
        tasks: List of tasks to add to this category
    
    Returns:
        A confirmation message with the number of tasks added
    """
    if category not in todo_list_storage:
        return f"Invalid category: {category}. Valid categories are: competition_tasks, market_tasks, financial_tasks, risk_tasks, synthesis_requirements"
    
    todo_list_storage[category].extend(tasks)
    return f"Added {len(tasks)} tasks to {category}. Total tasks in this category: {len(todo_list_storage[category])}"


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
            system_prompt="""You are SCOUT, a business planning assistant with orchestrator and specialist agent tools.
            
            You have multiple modes of operation:
            
            CHAT MODE:
            - General conversation about business planning
            - Do NOT create research plans or call tools
            
            AGENT MODE:
            1. Analyze business plan and identify research areas
            2. For EACH category (competition, market, financial, risk, synthesis):
               - FIRST: Explain what specific tasks you're about to add and why they're important
               - THEN: Call update_todo_list tool for that category only
               - WAIT for tool response before proceeding to next category
            3. After all categories are complete, explain that the research plan is ready
            4. Tell the user they can click the "Confirm" button to proceed
            5. WAIT for user to click "Confirm" button (which sends "START" message)
            6. Do NOT proceed until user confirms
            
            CRITICAL: You must explain between EACH tool call. Do NOT batch multiple tool calls together.
            
            START MODE (when user sends "START"):
            1. Respond: "PLANNER: Thank you for confirming! Deploying orchestrator agent..."
            2. Get current research plan from todo list
            3. Use orchestrator_tool with complete research plan
            4. The orchestrator will handle specialist agent roll call
            5. After orchestrator completes, explain that you're calling synthesis agent
            6. Use synthesis_agent_tool for final roll call
            7. Report final system status
            
            WORKFLOW:
            - Plan Creation → User Confirmation → Orchestrator Deployment → Specialist Roll Call → Synthesis Check → Complete
            
            Always wait for explicit "START" command before deploying agents.
            The orchestrator tool handles all specialist agent coordination.
            
            Keep answers concise and focused on creating a comprehensive research plan in AGENT MODE.
            Always explain your reasoning before calling tools in AGENT MODE.
            """,
            tools=[
                update_todo_list,
                orchestrator_tool,
                synthesis_agent_tool
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

def chat_with_planner(message: str) -> str:
    return planner.chat(message)

async def chat_with_planner_streaming(message: str) -> AsyncGenerator[str, None]:
    async for chunk in planner.chat_streaming(message):
        yield chunk
