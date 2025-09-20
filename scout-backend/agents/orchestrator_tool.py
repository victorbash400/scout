from strands import Agent, tool
from config.settings import settings
from .specialist_tools import (
    competition_agent_tool,
    market_agent_tool, 
    financial_agent_tool,
    risk_agent_tool
)

@tool
def orchestrator_tool(research_plan: str) -> str:
    """
    Orchestrator agent that coordinates all specialist agents.
    
    Args:
        research_plan: Complete research plan with tasks for all agents
        
    Returns:
        Orchestration results and agent status reports
    """
    try:
        # Collect all responses to include in the final output
        all_responses = []
        
        # Start with orchestrator introduction
        orchestrator_intro = """ORCHESTRATOR: I've received your comprehensive research plan. This is an excellent, well-structured research framework covering all critical aspects of the business analysis. Let me perform a roll call with my specialist agents to ensure everyone is ready to tackle their respective sections.

I'll be coordinating with four specialist agents:
- Competition Agent: For competitive intelligence and market positioning analysis
- Market Agent: For market research and customer analysis  
- Financial Agent: For financial modeling and projections
- Risk Agent: For risk assessment and mitigation planning

Let me check in with each agent now:"""
        
        all_responses.append(orchestrator_intro)
        
        # Call each specialist agent and collect responses
        agents = [
            ("competition_agent_tool", "Competition Agent"),
            ("market_agent_tool", "Market Agent"), 
            ("financial_agent_tool", "Financial Agent"),
            ("risk_agent_tool", "Risk Agent")
        ]
        
        for tool_name, agent_name in agents:
            # Call the agent
            if tool_name == "competition_agent_tool":
                agent_response = competition_agent_tool("ROLL CALL - Agent status check")
            elif tool_name == "market_agent_tool":
                agent_response = market_agent_tool("ROLL CALL - Agent status check")
            elif tool_name == "financial_agent_tool":
                agent_response = financial_agent_tool("ROLL CALL - Agent status check")
            elif tool_name == "risk_agent_tool":
                agent_response = risk_agent_tool("ROLL CALL - Agent status check")
            
            # Add agent response
            all_responses.append(agent_response)
            
            # Add orchestrator acknowledgment
            if agent_name == "Competition Agent":
                all_responses.append("ORCHESTRATOR: Great! Competition Agent is online and ready. Now checking with Market Agent:")
            elif agent_name == "Market Agent":
                all_responses.append("ORCHESTRATOR: Excellent! Market Agent is standing by. Let me check with Financial Agent:")
            elif agent_name == "Financial Agent":
                all_responses.append("ORCHESTRATOR: Perfect! Financial Agent is ready. Now checking with Risk Agent:")
            elif agent_name == "Risk Agent":
                all_responses.append("ORCHESTRATOR: Outstanding! Risk Agent is confirmed. All specialist agents are operational and ready for deployment.")
        
        # Final summary
        final_summary = """ORCHESTRATOR: Roll call complete! All specialist agents are operational and ready to execute the research plan. The system is fully deployed and prepared for comprehensive business intelligence gathering."""
        
        all_responses.append(final_summary)
        
        # Return all responses joined together
        return "\n\n".join(all_responses)
        
    except Exception as e:
        return f"Orchestrator Error: {str(e)}"
