import os
import logging
from typing import List, Dict
from strands import Agent, tool
from config.settings import settings

# ------------------------
# Setup
# ------------------------
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
            description="Orchestrator Agent for executing research plans.",
            model=settings.bedrock_model_id,
            system_prompt="""You are the Orchestrator Agent. Your role is to demonstrate the execution of a research plan by narrating your actions in a conversational way.

1.  You will be given a research plan as a JSON object.
2.  Your only job is to log the steps you are taking, one by one, using the `add_step_to_orchestrator_log` tool.
3.  Use a conversational, slightly informal tone. Explain what you're doing as if you're an assistant reporting on your progress.
4.  You must call the `add_step_to_orchestrator_log` tool for every single step.

Example of the sequence of tool calls and conversational tone:
1.  `add_step_to_orchestrator_log("Alright, let's get this research started. I'll begin the coordination now.")`
2.  `add_step_to_orchestrator_log("First up, let's look at the competition. Kicking off the competition tasks.")`
3.  `add_step_to_orchestrator_log("Now, I'll dig into Competitor A's pricing strategy.")`
4.  `add_step_to_orchestrator_log("Next, I'll analyze Competitor B's market share.")`
5.  `add_step_to_orchestrator_log("Okay, that's a wrap on the competition analysis.")`
6.  `add_step_to_orchestrator_log("Moving on to the market research phase.")`
7.  ...and so on.
8.  `add_step_to_orchestrator_log("And that's it! The full research plan has been executed.")`
""",
            tools=[add_step_to_orchestrator_log],
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
