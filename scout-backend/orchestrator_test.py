import traceback
from agents.orchestrator_agent import run_orchestrator

def test_orchestrator_execution():
    print("--- Starting Orchestrator Execution Test ---")
    
    # 1. Create a mock research plan, similar to what the Planner would create.
    mock_plan = {
        "competition_tasks": ["Analyze competitor A", "Analyze competitor B"],
        "market_tasks": ["Research target audience"],
        "price_tasks": ["Validate pricing strategy"],
        "legal_tasks": ["Check e-commerce regulations"]
    }
    print(f"Mock plan created: {mock_plan}\n")
    
    try:
        # 2. Call the run_orchestrator function directly, just like the planner's tool does.
        print("Calling run_orchestrator...")
        result = run_orchestrator(mock_plan)
        print("\n✅ SUCCESS: run_orchestrator completed without crashing.")
        print(f"Final result from orchestrator: {result}")
        
    except Exception as e:
        print("\n❌ FAILED: The call to run_orchestrator crashed.")
        print("--- ERROR ---")
        traceback.print_exc()
        print("-------------")

if __name__ == "__main__":
    test_orchestrator_execution()
