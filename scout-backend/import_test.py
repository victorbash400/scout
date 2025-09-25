import traceback

def test_imports():
    print("--- Starting Import Test ---")
    
    agents_to_test = [
        "agents.competition_agent",
        "agents.market_agent",
        "agents.price_agent",
        "agents.legal_agent",
        "agents.synthesis_agent",
        "agents.orchestrator_agent",
        "agents.planner_agent"
    ]
    
    all_successful = True
    
    for agent_module in agents_to_test:
        try:
            __import__(agent_module)
            print(f"✅ SUCCESS: Successfully imported {agent_module}")
        except Exception as e:
            all_successful = False
            print(f"❌ FAILED: Could not import {agent_module}")
            print("--- ERROR --- ")
            traceback.print_exc()
            print("-------------")
            
    print("\n--- Import Test Complete ---")
    if all_successful:
        print("\nConclusion: All agent modules imported successfully.")
    else:
        print("\nConclusion: One or more agent modules failed to import. See errors above.")

if __name__ == "__main__":
    test_imports()
