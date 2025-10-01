import asyncio
import os
from agents.synthesis_agent import run_synthesis_agent

async def test_synthesis_agent():
    """
    Test the synthesis agent by running it with existing report files
    """
    print("Testing Synthesis Agent...")
    
    # Look for existing report files in the reports directory
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    
    # Create some sample reports if they don't exist
    sample_reports = {
        "reports/competition_report.md": """# Competition Report

## Executive Summary
This report analyzes the competitive landscape for the business.

## Findings
- Major competitors identified in the area
- Pricing strategies analyzed
- Market positioning recommendations provided
""",
        "reports/market_report.md": """# Market Report

## Executive Summary
This report analyzes the market conditions and opportunities.

## Findings
- Market size: Medium
- Growth potential: High
- Target demographics identified
- Seasonal trends noted
""",
        "reports/price_report.md": """# Price Report

## Executive Summary
This report provides pricing analysis and recommendations.

## Findings
- Average price points in the market
- Competitive pricing analysis
- Pricing strategy recommendations
""",
        "reports/legal_report.md": """# Legal Report

## Executive Summary
This report covers legal and regulatory requirements.

## Findings
- Business licensing requirements
- Zoning compliance issues
- Regulatory compliance checklist
"""
    }
    
    # Create sample report files if they don't exist
    file_paths = []
    for path, content in sample_reports.items():
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        file_paths.append(path)
        print(f"Created/Verified: {path}")
    
    print(f"\nRunning synthesis agent with report files: {file_paths}")
    
    # Run the synthesis agent
    try:
        async for event in run_synthesis_agent(file_paths):
            # Clean, human-readable output only
            if isinstance(event, dict):
                # Print only when a tool is called or a final result is produced
                tool_name = event.get('tool_name') or event.get('delta', {}).get('toolUse', {}).get('name')
                if tool_name == 'save_final_report':
                    print("Final report has been saved.")
                elif tool_name == 'update_work_progress':
                    status = event.get('tool_input', event.get('delta', {}).get('toolUse', {}).get('input', {})).get('status', '')
                    task = event.get('tool_input', event.get('delta', {}).get('toolUse', {}).get('input', {})).get('task', '')
                    print(f"Progress update: {status} - {task}")
                elif tool_name == 'file_read':
                    path = event.get('tool_input', event.get('delta', {}).get('toolUse', {}).get('input', {})).get('path', '')
                    print(f"Reading file: {path}")
            # Print errors if present
            if isinstance(event, dict) and 'error' in event:
                print(f"Error: {event['error']}")
        print("\nSynthesis agent completed successfully!")
        
        # Check if final report was created
        final_report_path = "reports/final_report.md"
        if os.path.exists(final_report_path):
            print(f"✓ Final report created at: {final_report_path}")
            with open(final_report_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"Final report content preview:\n{content[:200]}...")
        else:
            print("✗ Final report was not created")
            
    except Exception as e:
        print(f"Error running synthesis agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_synthesis_agent())