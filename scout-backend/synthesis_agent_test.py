"""
Test for Synthesis Agent
"""

def test_synthesis_agent():
    from agents.synthesis_agent import run_synthesis_agent
    print("--- Starting Synthesis Agent Test ---")
    try:
        result = run_synthesis_agent()
        print(f"✅ Synthesis Agent returned: {result}")
    except Exception as e:
        print("❌ FAILED: The call to run_synthesis_agent crashed.")
        print("--- ERROR ---")
        print(e)

if __name__ == "__main__":
    test_synthesis_agent()
