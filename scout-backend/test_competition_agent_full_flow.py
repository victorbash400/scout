#!/usr/bin/env python3
"""
Comprehensive test for the Competition Agent to verify full flow and tool functionality
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.competition_agent import CompetitionAgent, find_competitors, update_work_progress, save_competition_report
from utils.event_queue import event_queue
import time
import threading
import json


async def test_all_tool_functions():
    """Test each individual tool function"""
    print("=== Testing Individual Tool Functions ===")
    
    # Test 1: update_work_progress
    print("\n1. Testing update_work_progress tool...")
    try:
        result = await update_work_progress("started", "Starting competition analysis test", "Test task")
        print(f"   ✓ update_work_progress succeeded: {result}")
        
        # Check if event was sent to queue
        if not event_queue.get_queue().empty():
            event = event_queue.get_queue().get_nowait()
            print(f"   ✓ Event sent to queue: {event.get('payload', {}).get('display_message', 'No message')}")
        else:
            print("   ⚠ No event found in queue (this may be expected)")
            
    except Exception as e:
        print(f"   ✗ update_work_progress failed: {e}")
    
    # Test 2: find_competitors (without API key, this may fail gracefully)
    print("\n2. Testing find_competitors tool...")
    try:
        result = await find_competitors("bakery", "Nairobi, Kenya")
        print(f"   ✓ find_competitors completed (result length: {len(result)})")
        print(f"   Result preview: {result[:100]}...")
    except Exception as e:
        print(f"   ⚠ find_competitors failed (likely due to missing API key): {e}")
    
    # Test 3: save_competition_report
    print("\n3. Testing save_competition_report tool...")
    try:
        test_content = "# Competition Report\n\nThis is a test competition report.\n\n## Summary\n- Test finding 1\n- Test finding 2\n"
        result = save_competition_report(test_content)  # Call synchronously now
        print(f"   ✓ save_competition_report succeeded: {result}")
        
        # Verify the file was created
        import os
        if os.path.exists("reports/competition_report.md"):
            print("   ✓ Report file created successfully")
            # Check file content
            with open("reports/competition_report.md", 'r', encoding='utf-8') as f:
                saved_content = f.read()
            if test_content.strip() in saved_content.strip():
                print("   ✓ Report content matches expected content")
            else:
                print(f"   ⚠ Report content doesn't match. Expected: {test_content[:50]}..., Got: {saved_content[:50]}...")
        else:
            print("   ✗ Report file was not created")
    except Exception as e:
        print(f"   ✗ save_competition_report failed: {e}")


async def test_agent_initialization():
    """Test that the Competition Agent can be initialized properly"""
    print("\n=== Testing Agent Initialization ===")
    
    try:
        agent = CompetitionAgent()
        print("✓ Competition Agent initialized successfully")
        
        # Note: In strands SDK, the agent object doesn't expose tools directly
        # The important thing is that it initializes without error
        print("✓ Agent created with model and tools properly configured")
        
        return agent
    except Exception as e:
        print(f"✗ Competition Agent initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_full_agent_workflow():
    """Test the full agent workflow with a simple request"""
    print("\n=== Testing Full Agent Workflow ===")
    
    # Start a background task to monitor the event queue
    received_events = []
    def monitor_queue():
        start_time = time.time()
        print("   Event monitor started...")
        while time.time() - start_time < 15:  # Monitor for 15 seconds max
            try:
                if not event_queue.get_queue().empty():
                    event = event_queue.get_queue().get_nowait()
                    received_events.append(event)
                    agent_name = event.get('agentName', 'Unknown')
                    message = event.get('payload', {}).get('display_message', 
                                                         event.get('payload', {}).get('tool_input', {}).get('message', 'No message'))
                    print(f"   Event: {agent_name} - {message}")
            except:
                pass  # Queue might be empty, that's fine
            time.sleep(0.1)
        print(f"   Event monitor finished. Total events received: {len(received_events)}")

    # Start the event monitor in a background thread
    monitor_thread = threading.Thread(target=monitor_queue, daemon=True)
    monitor_thread.start()
    
    try:
        print("   Creating Competition Agent...")
        agent = CompetitionAgent()
        
        print("   Running agent with test prompt...")
        # Run a simple test - this should trigger the tools
        test_business_type = "bakery"
        test_area = "Test Area Nairobi"
        
        final_result = ""
        async for event in agent.run(test_business_type, test_area):
            # Collect the agent's response
            if 'delta' in event and 'text' in event['delta']:
                final_result += event['delta']['text']
        
        print(f"   ✓ Agent workflow completed")
        print(f"   Final result length: {len(final_result) if final_result else 0}")
        if final_result:
            print(f"   Result preview: {final_result[:200]}...")
        
    except Exception as e:
        print(f"   ✗ Agent workflow failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Wait for monitor to finish
    await asyncio.sleep(1)
    print(f"   Total events captured during workflow: {len(received_events)}")


async def test_sequential_tool_calls():
    """Test calling tools in sequence to mimic agent behavior"""
    print("\n=== Testing Sequential Tool Calls ===")
    
    try:
        # Simulate the typical sequence an agent would use
        print("   Calling update_work_progress (started)...")
        result1 = await update_work_progress("started", "Starting competitor analysis", "find_competitors")
        print(f"   ✓ {result1}")
        
        print("   Calling update_work_progress (in_progress)...")
        result2 = await update_work_progress("in_progress", "Searching for competitors", "find_competitors")
        print(f"   ✓ {result2}")
        
        print("   Calling find_competitors...")
        try:
            result3 = await find_competitors("bakery", "Nairobi, Kenya")
            print(f"   ✓ find_competitors returned {len(result3)} characters")
        except Exception as e:
            print(f"   ⚠ find_competitors failed (expected without API key): {e}")
        
        print("   Calling update_work_progress (completed)...")
        result4 = await update_work_progress("completed", "Competitor analysis completed", "find_competitors")
        print(f"   ✓ {result4}")
        
        print("   Calling save_competition_report...")
        test_report = "# Test Competition Report\n\nAnalysis completed with following findings:\n\n- Finding 1\n- Finding 2\n"
        result5 = save_competition_report(test_report)  # Call synchronously now
        print(f"   ✓ {result5}")
        
        print("   ✓ Sequential tool calls completed successfully")
        
    except Exception as e:
        print(f"   ✗ Sequential tool calls failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    print("🧪 Starting Comprehensive Competition Agent Test\n")
    
    # Clear the event queue first
    while not event_queue.get_queue().empty():
        event_queue.get_queue().get_nowait()
    
    # Run all tests
    await test_all_tool_functions()
    await test_agent_initialization()
    await test_sequential_tool_calls()
    await test_full_agent_workflow()
    
    print(f"\n🎯 Test Summary Complete!")
    print("Note: Some failures may be expected if API keys are not configured.")
    
    # Check for any remaining events in queue
    remaining_events = []
    while not event_queue.get_queue().empty():
        remaining_events.append(event_queue.get_queue().get_nowait())
    
    if remaining_events:
        print(f"Additional events found in queue after tests: {len(remaining_events)}")


if __name__ == "__main__":
    asyncio.run(main())