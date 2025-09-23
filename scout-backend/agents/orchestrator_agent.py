import os
import asyncio
import logging
import json
from typing import AsyncGenerator, Dict, List
from strands import Agent, tool
from strands.multiagent.a2a import A2AServer
from dotenv import load_dotenv
from config.settings import settings

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global storage for received plans and coordination state
received_plans_storage: List[Dict] = []
coordination_status: Dict[str, str] = {}

class OrchestratorEventHandler:
    """Custom callback handler to capture orchestrator events and send to main.py via HTTP"""
    
    def __init__(self):
        self.webhook_url = "http://localhost:8000/api/orchestrator/events"
        logger.info("✅ Orchestrator event handler initialized with webhook")
    
    def __call__(self, **kwargs):
        """Send only final orchestrator messages to frontend"""
        try:
            # Only send final complete response
            if 'result' in kwargs:
                event_data = {
                    "type": "orchestrator_message",
                    "message": str(kwargs['result']),
                    "timestamp": asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
                }
                
                # Send HTTP POST to main.py webhook (non-blocking)
                import threading
                import requests
                
                def send_webhook():
                    try:
                        response = requests.post(
                            self.webhook_url, 
                            json=event_data, 
                            timeout=5.0
                        )
                        if response.status_code != 200:
                            logger.error(f"Webhook failed: {response.status_code}")
                    except Exception as e:
                        pass
                
                # Send in background thread to avoid blocking the agent
                threading.Thread(target=send_webhook, daemon=True).start()
                
        except Exception as e:
            logger.error(f"Error in orchestrator callback handler: {e}")
            logger.error(f"Kwargs were: {kwargs}")

@tool
def store_research_plan(plan_data: str, source_agent: str = "Unknown") -> str:
    """
    Store a received research plan and prepare for coordination.
    
    Args:
        plan_data: The research plan content
        source_agent: The agent that sent the plan
        
    Returns:
        Confirmation message with plan ID
    """
    plan_id = f"plan_{len(received_plans_storage) + 1}"
    
    plan_record = {
        "id": plan_id,
        "data": plan_data,
        "source": source_agent,
        "status": "received",
        "timestamp": asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
    }
    
    received_plans_storage.append(plan_record)
    coordination_status[plan_id] = "pending_coordination"
    
    logger.info(f"Stored research plan {plan_id} from {source_agent}")
    return f"Research plan {plan_id} stored successfully. Status: ready for coordination."

@tool
def get_coordination_status(plan_id: str = None) -> str:
    """
    Get the coordination status for a specific plan or all plans.
    
    Args:
        plan_id: Optional specific plan ID to check
        
    Returns:
        Status information
    """
    if plan_id:
        if plan_id in coordination_status:
            return f"Plan {plan_id} status: {coordination_status[plan_id]}"
        else:
            return f"Plan {plan_id} not found."
    else:
        if not coordination_status:
            return "No plans currently being coordinated."
        
        status_summary = "Coordination Status Summary:\n"
        for pid, status in coordination_status.items():
            status_summary += f"- {pid}: {status}\n"
        return status_summary

@tool
def update_coordination_status(plan_id: str, status: str) -> str:
    """
    Update the coordination status for a plan.
    
    Args:
        plan_id: The plan ID to update
        status: New status (e.g., 'in_progress', 'completed', 'failed')
        
    Returns:
        Confirmation message
    """
    if plan_id not in coordination_status:
        return f"Plan {plan_id} not found."
    
    old_status = coordination_status[plan_id]
    coordination_status[plan_id] = status
    
    logger.info(f"Updated {plan_id} status from {old_status} to {status}")
    return f"Plan {plan_id} status updated from {old_status} to {status}."

class OrchestratorAgent:
    def __init__(self):
        # Load AWS credentials
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region
        logger.info("✅ AWS credentials loaded successfully")

        # Create A2A client tools for communicating with other agents
        try:
            from strands_tools.a2a_client import A2AClientToolProvider
            a2a_provider = A2AClientToolProvider(
                known_agent_urls=[
                    "http://127.0.0.1:9000",  # Planner agent
                    # Add other specialist agent URLs here as they come online
                ]
            )
            a2a_tools = a2a_provider.tools
            logger.info(f"✅ A2A client tools loaded: {len(a2a_tools)} tools available")
        except Exception as e:
            logger.warning(f"Could not load A2A client tools: {e}")
            a2a_tools = []

        self.agent = Agent(
            name="SCOUT Orchestrator Agent",
            description="SCOUT's Orchestrator Agent that receives research plans and coordinates specialist agents via A2A protocol.",
            model=settings.bedrock_model_id,
            system_prompt="""You are SCOUT's Orchestrator Agent with A2A communication capabilities.
            
            Your primary responsibilities:
            1. Receive research plans from the Planner Agent and other agents via A2A communication
            2. Store and acknowledge receipt of plans with clear confirmation
            3. Coordinate the execution of research tasks with specialist agents
            4. Provide status updates and progress tracking
            5. Communicate back to requesting agents when tasks are complete
            
            When you receive a research plan:
            1. Use the store_research_plan tool to save it
            2. Acknowledge receipt with a clear confirmation message that includes:
               - Confirmation that you received the plan
               - Summary of the key components you understand
               - The plan ID for tracking
               - Your readiness to coordinate specialist agents
            3. If the plan contains specific tasks for different categories, mention those categories
            
            You have tools to:
            - store_research_plan: Store incoming research plans
            - get_coordination_status: Check status of coordination efforts
            - update_coordination_status: Update progress on plan execution
            - A2A communication tools: Send messages to other agents in the system
            
            You are currently in TEST MODE - you will acknowledge plans and confirm receipt.
            In future phases, you will coordinate with specialist agents for:
            - Competition analysis agents
            - Market research agents  
            - Financial analysis agents
            - Risk assessment agents
            - Synthesis and reporting agents
            
            Always be professional, clear, and confirmatory in your responses.
            Focus on demonstrating that you have received, understood, and stored the research plan.
            Provide specific plan IDs for tracking purposes.
            """,
            tools=[
                store_research_plan, 
                get_coordination_status, 
                update_coordination_status
            ] + a2a_tools,
            callback_handler=OrchestratorEventHandler()  # ADD CALLBACK HANDLER
        )
        
        logger.info(f"✅ Orchestrator Agent initialized with {settings.bedrock_model_id}")

    def chat(self, message: str) -> str:
        """Process incoming messages from other agents."""
        response = self.agent(message)
        return str(response.message)

    async def chat_streaming(self, message: str) -> AsyncGenerator[dict, None]:
        """Process incoming messages with streaming response."""
        try:
            async for event in self.agent.stream_async(message):
                yield event
        except Exception as e:
            yield {"error": str(e)}

    def get_plan_count(self) -> int:
        """Get the number of plans received."""
        return len(received_plans_storage)

    def get_all_plans(self) -> List[Dict]:
        """Get all stored plans."""
        return received_plans_storage.copy()

# Global orchestrator instance
orchestrator = OrchestratorAgent()

def chat_with_orchestrator(message: str) -> str:
    """Chat with the orchestrator agent."""
    return orchestrator.chat(message)

async def chat_with_orchestrator_streaming(message: str) -> AsyncGenerator[str, None]:
    """Stream chat with the orchestrator agent."""
    async for chunk in orchestrator.chat_streaming(message):
        yield chunk

def get_orchestrator_status() -> Dict:
    """Get orchestrator status and stored plans."""
    return {
        "plan_count": orchestrator.get_plan_count(),
        "coordination_status": coordination_status.copy(),
        "plans": orchestrator.get_all_plans()
    }

# A2A Server setup
def create_orchestrator_a2a_server(port: int = 9001):
    """Create and return the A2A server for the orchestrator agent."""
    try:
        # Use the global orchestrator instance's agent for the A2A server
        a2a_server = A2AServer(
            agent=orchestrator.agent,
            host="127.0.0.1",
            port=port,
            version="1.0.0"
        )
        logger.info(f"✅ Orchestrator A2A Server created on port {port}")
        return a2a_server
    except Exception as e:
        logger.error(f"Error creating orchestrator A2A server: {e}")
        raise

if __name__ == "__main__":
    # Start the orchestrator A2A server
    server = create_orchestrator_a2a_server()
    logger.info("Starting Orchestrator A2A Server on port 9001...")
    server.serve()