import os
from agents.market_agent import run_market_agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_market_agent():
    # Example: Analyze a known business type in a well-known area
    business_type = "bakery"
    area = "Manhattan, New York, NY"
    tasks = [business_type, area]
    print(f"Testing Market Agent with: {business_type} in {area}")
    result = run_market_agent(tasks)
    print("\n--- MARKET AGENT'S FINAL REPORT ---")
    print(result)
    print("-----------------------------------\n")

if __name__ == "__main__":
    test_market_agent()
