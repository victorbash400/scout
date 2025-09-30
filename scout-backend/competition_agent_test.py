
import asyncio
from agents.competition_agent import run_competition_agent
from dotenv import load_dotenv

load_dotenv()

def test_competition_agent():
    business_type = "bakery"
    area = "Manhattan, New York, NY"
    tasks = [business_type, area]
    print(f"Testing Competition Agent with: {business_type} in {area}")
    result = asyncio.run(run_competition_agent(tasks))
    print("\n--- AGENT'S FINAL REPORT ---")
    print(result)
    print("----------------------------\n")

if __name__ == "__main__":
    test_competition_agent()
