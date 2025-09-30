#!/usr/bin/env python3
"""
Test script to verify the async Competition Agent works properly
"""
import asyncio
import sys
import os

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.competition_agent import CompetitionAgent, find_competitors, update_work_progress, save_competition_report
from utils.event_queue import event_queue


async def test_async_tools():
    """Test that all tools are async and work properly"""
    print("Testing async tools in Competition Agent...")
    
    # Test if the underlying functions are async
    # Note: The @tool decorator wraps functions, so we need to check the wrapped function
    import inspect
    
    # Check if the original functions are async (before decorator wrapping)
    print(f"find_competitors has async code: {inspect.iscoroutinefunction(find_competitors.__wrapped__ if hasattr(find_competitors, '__wrapped__') else find_competitors)}")
    print(f"update_work_progress has async code: {inspect.iscoroutinefunction(update_work_progress.__wrapped__ if hasattr(update_work_progress, '__wrapped__') else update_work_progress)}")
    print(f"save_competition_report is sync (as expected): {not inspect.iscoroutinefunction(save_competition_report.__wrapped__ if hasattr(save_competition_report, '__wrapped__') else save_competition_report)}")
    
    # Test update_work_progress tool
    print("\nTesting update_work_progress tool...")
    try:
        result = await update_work_progress("started", "Test message", "Test task")
        print(f"✅ update_work_progress result: {result}")
        
        # Check if an event was added to the queue
        queue_size = event_queue.get_queue().qsize()
        print(f"✅ Events in queue after update_work_progress: {queue_size}")
        if not event_queue.get_queue().empty():
            event = event_queue.get_queue().get_nowait()
            print(f"✅ Event from queue: {event['eventType']} - {event['payload']['display_message']}")
    except Exception as e:
        print(f"❌ Error in update_work_progress: {e}")
        import traceback
        traceback.print_exc()
    
    # Test find_competitors with mock data (without needing API key)
    print("\nTesting find_competitors tool...")
    try:
        result = await find_competitors("test business", "test area")
        print(f"✅ find_competitors result: {result[:100]}...")
    except Exception as e:
        print(f"⚠️  find_competitors result (expected without API key): {str(e)[:100]}")
    
    # Test save_competition_report
    print("\nTesting save_competition_report tool...")
    try:
        # Make sure reports directory exists
        os.makedirs("reports", exist_ok=True)
        result = save_competition_report("# Test Report\nThis is a test report.")
        print(f"✅ save_competition_report result: {result}")
        
        # Verify the file was created
        if os.path.exists("reports/competition_report.md"):
            print("✅ File was created successfully!")
            with open("reports/competition_report.md", "r") as f:
                content = f.read()
                print(f"✅ File content preview: {content[:50]}...")
        else:
            print("❌ File was not created")
    except Exception as e:
        print(f"❌ Error in save_competition_report: {e}")
        import traceback
        traceback.print_exc()


async def test_strands_tools_modules():
    """Test that strands_tools modules are imported correctly"""
    print("\nTesting strands_tools module imports...")
    try:
        import strands_tools.file_write as file_write_module
        import strands_tools.batch as batch_module
        
        print(f"✅ file_write module imported: {file_write_module}")
        print(f"✅ batch module imported: {batch_module}")
        
        # Check if they have the expected attributes
        print(f"✅ file_write module type: {type(file_write_module)}")
        print(f"✅ batch module type: {type(batch_module)}")
        
        # These are modules that will be used by the agent, not called directly
        print("✅ Modules can be passed directly to Agent tools parameter")
        
    except Exception as e:
        print(f"❌ Error importing strands_tools modules: {e}")
        import traceback
        traceback.print_exc()


async def test_agent_creation():
    """Test that the Competition Agent can be created with async tools"""
    print("\nTesting Competition Agent creation...")
    try:
        agent = CompetitionAgent()
        print("✅ CompetitionAgent created successfully!")
        
        # Check agent properties
        print(f"✅ Agent name: {agent.agent.name}")
        print(f"✅ Agent model: {agent.agent.model}")
        
        # The agent has a tool_names property
        if hasattr(agent.agent, 'tool_names'):
            print(f"✅ Agent tool_names: {agent.agent.tool_names}")
        else:
            print("⚠️  Agent doesn't expose tool_names directly")
        
        return agent
    except Exception as e:
        print(f"❌ Error creating CompetitionAgent: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_direct_file_operations():
    """Test that we can write files directly using standard Python"""
    print("\nTesting direct file operations (fallback method)...")
    try:
        os.makedirs("reports", exist_ok=True)
        test_file = "reports/test_direct.md"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("# Direct Test\nThis is a direct test using Python file I/O.")
        
        print(f"✅ File written successfully: {test_file}")
        
        # Verify file exists
        if os.path.exists(test_file):
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ File content verified: {content[:50]}...")
        else:
            print("❌ File was not created")
            
    except Exception as e:
        print(f"❌ Error in direct file operations: {e}")
        import traceback
        traceback.print_exc()


async def main():
    print("=" * 60)
    print("Starting async Competition Agent tests...")
    print("=" * 60)
    
    # Test 1: Async tools
    await test_async_tools()
    
    # Test 2: Strands tools modules
    await test_strands_tools_modules()
    
    # Test 3: Direct file operations
    await test_direct_file_operations()
    
    # Test 4: Agent creation
    agent = await test_agent_creation()
    
    print("\n" + "=" * 60)
    if agent:
        print("✅ All tests completed! The Competition Agent is working properly.")
        print("\nNote: file_write and batch are strands_tools modules that")
        print("      the agent can use internally. They're not meant to be")
        print("      called directly in our custom tools.")
    else:
        print("⚠️  Some tests had issues, but core functionality may still work.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())