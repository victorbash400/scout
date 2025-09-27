import os
import ast
from agents.synthesis_agent import run_synthesis_agent

def test_synthesis_agent():
    """Tests the synthesis agent without using pytest."""
    print("--- Starting Synthesis Agent Test ---")
    reports_dir = "C:/Users/Victo/Desktop/Scout/scout-backend/reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    dummy_files = []
    dummy_content = {
        "competition_report.md": "# Competition Analysis\n\n- Competitor A\n- Competitor B",
        "market_report.md": "# Market Analysis\n\n- Market Size: $1B\n- Target Audience: Millennials",
    }

    try:
        # Create dummy files
        for filename, content in dummy_content.items():
            filepath = os.path.join(reports_dir, filename)
            with open(filepath, "w") as f:
                f.write(content)
            dummy_files.append(filepath)
        print(f"Created dummy reports: {dummy_files}")

        # Run the synthesis agent
        result_str = run_synthesis_agent(dummy_files)
        print(f"Synthesis agent returned: {result_str}")

        # Safely evaluate the string representation of the dictionary
        try:
            result_dict = ast.literal_eval(result_str)
            message_text = result_dict.get('content', [{}])[0].get('text', '')
        except (ValueError, SyntaxError):
            message_text = result_str

        # Check that the agent returns a success message
        if "synthesis complete" not in message_text.lower():
            print(f"❌ FAILED: Agent did not return a success message. Actual message: {message_text}")
            return

        # Check that the final report was created
        final_report_path = os.path.join(reports_dir, "final_report.md")
        if not os.path.exists(final_report_path):
            print("❌ FAILED: Final report file was not created.")
            return
        
        print(f"✅ Final report created at: {final_report_path}")

        # Check that the final report has content
        with open(final_report_path, "r") as f:
            content = f.read()
        
        if not content:
            print("❌ FAILED: Final report is empty.")
            return

        print("\n--- FINAL REPORT CONTENT ---")
        print(content)
        print("----------------------------")
        print("\n✅ Synthesis Agent Test Passed!")

    except Exception as e:
        print(f"❌ FAILED: An exception occurred during the test: {e}")
    finally:
        # Cleanup
        print("\n--- Cleaning up created files ---")
        for filepath in dummy_files:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Removed: {filepath}")
        final_report_path = os.path.join(reports_dir, "final_report.md")
        if os.path.exists(final_report_path):
            os.remove(final_report_path)
            print(f"Removed: {final_report_path}")

if __name__ == "__main__":
    test_synthesis_agent()