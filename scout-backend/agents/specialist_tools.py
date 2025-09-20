from strands import Agent, tool
from config.settings import settings

@tool
def competition_agent_tool(message: str) -> str:
    """
    Competitive intelligence specialist agent as a tool.
    
    Args:
        message: Research task or roll call request
        
    Returns:
        Agent response confirming receipt and status
    """
    try:
        competition_agent = Agent(
            model=settings.bedrock_model_id,
            system_prompt="""
            You are SCOUT's Competition Intelligence Agent. You are an AI agent that streams responses.
            
            **ROLL CALL MODE**: If message contains "ROLL CALL":
            - Respond naturally: "COMPETITION AGENT: Present! I'm ready to analyze your competitive landscape. Standing by for competitive intelligence tasks."
            
            **TASK MODE**: When you receive actual research tasks:
            - Respond: "COMPETITION AGENT: Received competition research tasks. Beginning competitive analysis..."
            - For now, just confirm receipt - actual research tools will be added later
            
            You should respond naturally and conversationally, not just with status messages.
            """
        )
        
        response = competition_agent(message)
        return str(response)
        
    except Exception as e:
        return f"Competition Agent Error: {str(e)}"

@tool
def market_agent_tool(message: str) -> str:
    """
    Market analysis specialist agent as a tool.
    
    Args:
        message: Research task or roll call request
        
    Returns:
        Agent response confirming receipt and status
    """
    try:
        market_agent = Agent(
            model=settings.bedrock_model_id,
            system_prompt="""
            You are SCOUT's Market Analysis Agent. You are an AI agent that streams responses.
            
            **ROLL CALL MODE**: If message contains "ROLL CALL":
            - Respond naturally: "MARKET AGENT: Present! I'm ready to analyze your target market and validate demand. Standing by for market analysis tasks."
            
            **TASK MODE**: When you receive actual research tasks:
            - Respond: "MARKET AGENT: Received market research tasks. Beginning market analysis..."
            
            You should respond naturally and conversationally, not just with status messages.
            """
        )
        
        response = market_agent(message)
        return str(response)
        
    except Exception as e:
        return f"Market Agent Error: {str(e)}"

@tool
def financial_agent_tool(message: str) -> str:
    """
    Financial modeling specialist agent as a tool.
    
    Args:
        message: Research task or roll call request
        
    Returns:
        Agent response confirming receipt and status
    """
    try:
        financial_agent = Agent(
            model=settings.bedrock_model_id,
            system_prompt="""
            You are SCOUT's Financial Analysis Agent. You are an AI agent that streams responses.
            
            **ROLL CALL MODE**: If message contains "ROLL CALL":
            - Respond naturally: "FINANCIAL AGENT: Present! I'm ready to analyze your financial projections and validate your business model. Standing by for financial modeling tasks."
            
            **TASK MODE**: When you receive actual research tasks:
            - Respond: "FINANCIAL AGENT: Received financial analysis tasks. Beginning financial modeling..."
            
            You should respond naturally and conversationally, not just with status messages.
            """
        )
        
        response = financial_agent(message)
        return str(response)
        
    except Exception as e:
        return f"Financial Agent Error: {str(e)}"

@tool
def risk_agent_tool(message: str) -> str:
    """
    Risk assessment specialist agent as a tool.
    
    Args:
        message: Research task or roll call request
        
    Returns:
        Agent response confirming receipt and status
    """
    try:
        risk_agent = Agent(
            model=settings.bedrock_model_id,
            system_prompt="""
            You are SCOUT's Risk Assessment Agent. You are an AI agent that streams responses.
            
            **ROLL CALL MODE**: If message contains "ROLL CALL":
            - Respond naturally: "RISK AGENT: Present! I'm ready to identify and assess potential risks to your business. Standing by for risk analysis tasks."
            
            **TASK MODE**: When you receive actual research tasks:
            - Respond: "RISK AGENT: Received risk assessment tasks. Beginning risk analysis..."
            
            You should respond naturally and conversationally, not just with status messages.
            """
        )
        
        response = risk_agent(message)
        return str(response)
        
    except Exception as e:
        return f"Risk Agent Error: {str(e)}"

@tool
def synthesis_agent_tool(message: str) -> str:
    """
    Synthesis and reporting specialist agent as a tool.
    
    Args:
        message: Compilation request or roll call
        
    Returns:
        Agent response confirming synthesis capabilities
    """
    try:
        synthesis_agent = Agent(
            model=settings.bedrock_model_id,
            system_prompt="""
            You are SCOUT's Synthesis Agent. You are an AI agent that streams responses.
            
            **ROLL CALL MODE**: If message contains "ROLL CALL":
            - Respond naturally: "SYNTHESIS AGENT: Present! I'm ready to synthesize all research findings into a comprehensive intelligence report. Standing by for intelligence synthesis and report generation."
            
            **SYNTHESIS MODE**: When you receive compiled research:
            - Respond: "SYNTHESIS AGENT: Received compiled intelligence from agents. Beginning report synthesis..."
            
            You should respond naturally and conversationally, not just with status messages.
            """
        )
        
        response = synthesis_agent(message)
        return str(response)
        
    except Exception as e:
        return f"Synthesis Agent Error: {str(e)}"
