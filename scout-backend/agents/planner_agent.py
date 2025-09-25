import os
import asyncio
import logging
from typing import AsyncGenerator, List, Dict
from strands import Agent, tool
from dotenv import load_dotenv
from config.settings import settings
from agents.orchestrator_agent import run_orchestrator

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@tool
def execute_research_plan() -> str:
    """
    Executes the research plan by calling the orchestrator agent.
    This should be called after the user has approved the plan.
    """
    global todo_list_storage
    logger.info("Executing research plan...")
    result = run_orchestrator(todo_list_storage)
    return f"Orchestrator finished with result: {result}"

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
            1. Analyze the business plan and identify key areas for research
            2. Create a structured to-do list with specific tasks for different specialist agents
            3. BEFORE calling EACH update_todo_list tool, EXPLAIN to the user:
               - What specific tasks you're about to add
               - Why these tasks are important for the research plan
               - Which category they belong to
            4. Then use the update_todo_list tool to add tasks to the appropriate category and repeat for each tool call
            5. After completing the plan, ask the user if they are satisfied with the plan and if you should send the plan to the orchestrator.
            6. If user confirms, BEFORE calling the execute_research_plan tool, EXPLAIN to the user:
               - What you're about to send to the orchestrator
               - Why you're sending it now
               - What the orchestrator will do with it
            7. Then use the execute_research_plan tool to send the complete plan to the orchestrator.
               
            The to-do list categories are:
            - competition_tasks: Direct competitor analysis, pricing intelligence, market positioning, financial intelligence
            - market_tasks: Customer demographics, market sizing, demand validation, geographic analysis
            - financial_tasks: Unit economics modeling, pricing strategy, financial projections, investment analysis
            - risk_tasks: Regulatory compliance, market risks, operational risks, competitive threats, strategic risks
            - synthesis_requirements: Executive summary, strategic recommendations, visual intelligence
            
            You will be told which mode you are in at the beginning of each conversation.
            In CHAT MODE, do NOT create research plans or call tools.
            In AGENT MODE, follow the structured research plan creation process.
            
            Example interaction in AGENT MODE:
            User: "I have a food delivery business plan"
            Assistant: "I'll analyze this plan and create research tasks. Let me first identify the key competitors we should research."
            Assistant: "let me  add competitor analysis tasks to the competition_tasks category because understanding the competitive landscape is crucial for your market entry strategy."
            Assistant: [Tool call to update_todo_list with competition tasks]
            Assistant: "Now I'll focus on market sizing since we need to understand the total addressable market for your service."
            Assistant: [Tool call to update_todo_list with market sizing tasks]
            ... (after plan is complete)
            Assistant: "I have completed the research plan. Are you satisfied with it and should I send it to the orchestrator to begin execution?"
            User: "Yes, looks good. Go ahead."
            Assistant: "Great. I am now sending the plan to the orchestrator. The orchestrator will now execute the research tasks by using specialist agents. You will see the progress in the right panel."
            Assistant: [Tool call to execute_research_plan]
            
            Keep answers concise and focused on creating a comprehensive research plan in AGENT MODE.
            Always explain your reasoning before calling tools in AGENT MODE.
            """,
            tools=[update_todo_list, execute_research_plan]
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