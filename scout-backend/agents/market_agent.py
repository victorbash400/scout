import os
import requests
import logging
import time
from typing import List
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from strands import Agent, tool
from config.settings import settings

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Improved Perplexity API Helper Function with Timeout and Retry ---
def _call_perplexity_api(query: str, timeout: int = 30, max_retries: int = 2) -> str:
    """
    A helper function to call the Perplexity Sonar API with timeout and retry logic.
    
    Args:
        query: The search query
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum number of retry attempts (default: 2)
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return "Error: PERPLEXITY_API_KEY is not set in the environment."

    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar",
        "messages": [{"role": "user", "content": query}],
        "max_tokens": 1000,  # Add explicit max_tokens
        "temperature": 0.1   # Add temperature for consistency
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Making Perplexity API call (attempt {attempt + 1}/{max_retries + 1})")
            
            # Use ThreadPoolExecutor to implement timeout
            with ThreadPoolExecutor() as executor:
                future = executor.submit(requests.post, url, json=payload, headers=headers, timeout=timeout)
                try:
                    response = future.result(timeout=timeout + 5)  # Add buffer to thread timeout
                except TimeoutError:
                    logger.error(f"Request timed out after {timeout} seconds")
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return f"Error: Request timed out after {timeout} seconds. Please try again with a simpler query."

            response.raise_for_status()
            
            # Parse JSON response
            try:
                data = response.json()
            except ValueError as json_error:
                logger.error(f"Failed to parse JSON response: {json_error}")
                logger.error(f"Response content: {response.text}")
                return f"Error: Invalid JSON response from API. Response: {response.text[:200]}..."
            
            # Validate response structure
            if not isinstance(data, dict):
                logger.error(f"Expected dict, got {type(data)}: {data}")
                return f"Error: Unexpected response format from API"
            
            # Extract content safely
            choices = data.get("choices", [])
            if not choices:
                logger.error("No choices in API response")
                return "Error: No content returned from API"
            
            message = choices[0].get("message", {}) if choices else {}
            content = message.get("content", "No content found.")
            
            # Extract citations - they can be either strings or objects
            citations = data.get("citations", [])
            
            # Extract citations - prioritize actual URLs over summaries
            citations = data.get("citations", [])
            search_results = data.get("search_results", [])
            
            # Collect all available URLs
            all_urls = []
            
            # First, get URLs from citations
            if citations:
                for citation in citations:
                    if isinstance(citation, str):
                        # Citation is a direct URL string
                        all_urls.append(citation)
                    elif isinstance(citation, dict) and citation.get('url'):
                        # Citation is an object with URL field
                        all_urls.append(citation['url'])
            
            # If no citations, get URLs from search_results
            if not all_urls and search_results:
                for result in search_results:
                    if result.get('url'):
                        all_urls.append(result['url'])
            
            # Format the URLs if we have any
            if all_urls:
                sources_header = "\n\n**Sources:**\n"
                # Remove duplicates while preserving order
                unique_urls = []
                for url in all_urls:
                    if url not in unique_urls:
                        unique_urls.append(url)
                
                source_links = [f"- {url}" for url in unique_urls[:5]]  # Limit to top 5
                formatted_citations = sources_header + "\n".join(source_links)
                return content + formatted_citations
            
            return content
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error {e.response.status_code}"
            response_text = ""
            try:
                response_text = e.response.text if hasattr(e, 'response') and e.response else "No response body"
            except:
                response_text = "Could not read response body"
                
            if hasattr(e, 'response') and e.response:
                if e.response.status_code == 429:  # Rate limit
                    if attempt < max_retries:
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue
                    return "Error: Rate limit exceeded. Please try again later."
                elif e.response.status_code == 401:
                    return "Error: Invalid API key. Please check your PERPLEXITY_API_KEY."
                elif e.response.status_code == 400:
                    logger.error(f"Bad request: {response_text}")
                    return f"Error: Bad request to API. Check your query format."
                else:
                    logger.error(f"HTTP error: {error_msg}, Response: {response_text}")
                    if attempt < max_retries:
                        time.sleep(1)
                        continue
                    return f"Error: {error_msg}. Please try again."
            else:
                logger.error(f"HTTP error without response object: {e}")
                return f"Error: HTTP error occurred. {str(e)}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
                continue
            return f"Error: Network request failed. {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"Error: Unexpected error occurred. {str(e)}"
    
    return "Error: All retry attempts failed."


# --- Simplified Market Analysis Tools with Better Error Handling ---
@tool
def analyze_product_pricing(product: str, area: str) -> str:
    """
    Analyzes the average consumer price for a specific product in a given area.
    Use this to understand what customers are currently paying.
    
    Args:
        product: The product to analyze (e.g., "cup of coffee", "artisan bread")
        area: The geographic area (e.g., "Juja, Kiambu County")
    
    Returns:
        A string with pricing analysis and sources
    """
    try:
        logger.info(f"Starting product pricing analysis for '{product}' in '{area}'")
        query = f"What is the current average price of '{product}' in '{area}' Kenya in 2025? Include price ranges and factors affecting pricing."
        result = _call_perplexity_api(query, timeout=25)
        logger.info("Product pricing analysis completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in analyze_product_pricing: {e}")
        return f"Error analyzing product pricing: {str(e)}"

@tool
def analyze_local_economy(area: str) -> str:
    """
    Analyzes the general economic conditions of a specific area.
    
    Args:
        area: The geographic area to analyze
    
    Returns:
        A string with economic analysis and sources
    """
    try:
        logger.info(f"Starting local economy analysis for '{area}'")
        query = f"Provide an economic overview of '{area}' Kenya in 2025. Include average income levels, cost of living, and small business operating costs like rent."
        result = _call_perplexity_api(query, timeout=25)
        logger.info("Local economy analysis completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in analyze_local_economy: {e}")
        return f"Error analyzing local economy: {str(e)}"

@tool
def analyze_supplier_costs(business_type: str, area: str) -> str:
    """
    Analyzes the wholesale cost of raw materials for a business.
    
    Args:
        business_type: The type of business (e.g., "coffee shop", "bakery")
        area: The geographic area
    
    Returns:
        A string with supplier cost analysis and sources
    """
    try:
        logger.info(f"Starting supplier cost analysis for '{business_type}' in '{area}'")
        query = f"What are the wholesale costs for raw materials needed for a '{business_type}' in '{area}' Kenya in 2025? Include key ingredients and supplies."
        result = _call_perplexity_api(query, timeout=25)
        logger.info("Supplier cost analysis completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error in analyze_supplier_costs: {e}")
        return f"Error analyzing supplier costs: {str(e)}"


# --- MarketAgent Class with Improved Configuration ---
class MarketAgent:
    def __init__(self):
        # Set up AWS credentials
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region
            
        if not os.getenv("PERPLEXITY_API_KEY"):
            raise ValueError("PERPLEXITY_API_KEY environment variable not set.")
            
        # Improved system prompt with clearer instructions about preserving URLs
        system_prompt = """You are an expert Market Analyst. Your goal is to generate a detailed market and pricing landscape report for a new business.

        IMPORTANT: You MUST use your tools in this EXACT sequence:
        
        1. **First, analyze product pricing**: Call `analyze_product_pricing` to understand customer-facing prices for the main product/service.
        
        2. **Second, analyze the local economy**: Call `analyze_local_economy` to understand the economic environment and operating costs.
        
        3. **Third, analyze supplier costs**: Call `analyze_supplier_costs` to understand input costs and margins.
        
        4. **Finally, create a comprehensive report**: Combine all findings into a structured report with:
           - Executive Summary
           - Consumer Pricing Analysis (from tool 1)
           - Local Economic Environment (from tool 2)  
           - Supplier Cost Analysis (from tool 3)
           - Strategic Recommendations
        
        CRITICAL: When including sources , you MUST preserve the exact URLs returned by each tool. Do NOT rewrite or summarize the source URLs. If a tool returns "**Sources:**" followed by URLs, copy those URLs exactly as provided. Do not create generic source descriptions - use the actual clickable URLs.
        
        Always explain what you're doing before calling each tool. Be systematic and thorough."""
        
        try:
            self.agent = Agent(
                name="Market Agent",
                model=settings.bedrock_model_id,
                system_prompt=system_prompt,
                tools=[
                    analyze_product_pricing,
                    analyze_local_economy,
                    analyze_supplier_costs
                ]
            )
            logger.info("✅ Market Agent initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Market Agent: {e}")
            raise

    def run(self, business_type: str, area: str) -> str:
        """
        Run the market analysis for a given business type and area.
        """
        try:
            # Create a more specific prompt
            product_example = f"a key product from a {business_type}"
            if "coffee" in business_type.lower():
                product_example = "a cup of coffee"
            elif "bakery" in business_type.lower():
                product_example = "artisan bread"
            elif "restaurant" in business_type.lower():
                product_example = "a typical meal"
            
            prompt = (
                f"I need a comprehensive market analysis for opening a '{business_type}' in '{area}'. "
                f"Start by analyzing the pricing for {product_example}, then examine the local economy, "
                f"followed by supplier costs. Create a detailed report with all findings and sources."
            )
            
            logger.info(f"Starting market analysis for '{business_type}' in '{area}'")
            response = self.agent(prompt)
            logger.info("Market analysis completed successfully")
            return str(response.message)
            
        except Exception as e:
            logger.error(f"Error in MarketAgent.run: {e}")
            return f"Error generating market analysis: {str(e)}"


# --- Entry Point ---
market_agent_instance = None

def get_market_agent_instance():
    """Lazy initialization of the market agent instance."""
    global market_agent_instance
    if market_agent_instance is None:
        market_agent_instance = MarketAgent()
    return market_agent_instance

def run_market_agent(tasks: List[str]) -> str:
    """
    Entry point for the Market Agent, called by the Orchestrator.
    """
    if len(tasks) != 2:
        return "Error: The Market Agent requires exactly two tasks: a business type and an area."
        
    business_type, area = tasks
    logger.info(f"📈 Market Agent received tasks: Analyze '{business_type}' in '{area}'.")
    
    try:
        agent = get_market_agent_instance()
        return agent.run(business_type, area)
    except Exception as e:
        logger.error(f"Error in run_market_agent: {e}")
        return f"Error: Failed to run market analysis. {str(e)}"

# --- Example Usage ---
if __name__ == "__main__":
    test_tasks = ["high-end coffee shop", "Juja, Kiambu County"]
    analysis_result = run_market_agent(test_tasks)
    print("\n--- MARKET AGENT'S FINAL REPORT ---")
    print(analysis_result)
    print("-----------------------------------\n")