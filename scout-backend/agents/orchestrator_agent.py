import os
import logging
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

from strands import Agent, tool
from config.settings import settings

from agents.competition_agent import run_competition_agent
from agents.market_agent import run_market_agent
from agents.price_agent import run_price_agent
from agents.legal_agent import run_legal_agent

# ------------------------
# Setup
# ------------------------
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------
# Orchestrator Storage
# ------------------------
orchestrator_steps_storage: List[Dict[str, str]] = []

@tool
def add_step_to_orchestrator_log(step_description: str) -> str:
    """
    Adds a step to the orchestrator's log of actions.

    Args:
        step_description: A description of the step being performed.
    
    Returns:
        A confirmation that the step was logged.
    """
    global orchestrator_steps_storage
    orchestrator_steps_storage.append({"step": step_description})
    logger.info(f"Orchestrator step logged: {step_description}")
    return f"Step logged: {step_description}"

# ------------------------
# Specialist Agent Tools
# ------------------------
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

def get_orchestrator_steps() -> List[Dict[str, str]]:
    """
    Returns the current list of orchestrator steps.
    """
    return orchestrator_steps_storage

def clear_orchestrator_steps():
    """
    Clears the orchestrator's steps.
    """
    global orchestrator_steps_storage
    orchestrator_steps_storage = []

# ------------------------
# Orchestrator Agent
# ------------------------

class OrchestratorAgent:
    def __init__(self):
        # Load AWS credentials (optional)
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region
        
        self.agent = Agent(
            name="SCOUT Orchestrator",
            description="Orchestrator Agent for delegating tasks to specialist agents.",
            model=settings.bedrock_model_id,
            system_prompt="""You are the Orchestrator Agent. Your job is to coordinate a team of specialist agents.

1.  You will be given a research plan as a JSON object with keys like `competition_tasks`, `market_tasks`, etc.
2.  Your role is to perform a "roll call" by contacting each specialist agent that has tasks assigned to it in the plan.
3.  For each category in the plan, you must perform this single, consolidated step:
    a.  Simultaneously call the `add_step_to_orchestrator_log` tool to log your action **AND** call the corresponding specialist agent tool (`market_agent_tool`, `competition_agent_tool`, etc.), passing the list of tasks to it.
    b.  The log message should be brief and descriptive (e.g., "Contacting the Market Agent and delegating tasks.").
4.  Repeat this for all categories present in the plan.
5.  After all agents have been contacted, hand back to the Planner.
""",
            tools=[
                add_step_to_orchestrator_log,
                competition_agent_tool,
                market_agent_tool,
                price_agent_tool,
                legal_agent_tool
            ],
        )
        logger.info(f"✅ Orchestrator Agent initialized with {settings.bedrock_model_id}")

    def run(self, plan: Dict[str, List[str]]) -> str:
        """
        Runs the orchestration process on a given plan.
        """
        plan_str = str(plan)
        response = self.agent(f"Execute the following research plan: {plan_str}")
        return str(response.message)

# ------------------------
# Main Orchestrator Function (to be used as a tool)
# ------------------------
def run_orchestrator(plan: Dict[str, List[str]]) -> str:
    """
    This function is the entry point for the orchestrator agent.
    It takes a research plan, runs the orchestrator agent, and returns the result.
    """
    clear_orchestrator_steps()
    orchestrator = OrchestratorAgent()
    result = orchestrator.run(plan)
    return result
