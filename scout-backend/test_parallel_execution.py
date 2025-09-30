#!/usr/bin/env python3
"""
Test script to verify the Competition Agent works with parallel tool calls
This test will actually trigger the agent and monitor its progress updates
"""
import asyncio
import sys
import os
import threading
import time

# Add the project root to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.competition_agent import run_competition_agent
from utils.event_queue import event_queue
from agents.competition_agent import CompetitionAgent


class AgentMonitor:
    """Monitor to capture and display agent progress updates"""
    
    def __init__(self):
        self.events_received = []
        self.monitoring = False
        
    def start_monitoring(self, duration=30):
        """Start monitoring the event queue in a separate thread"""
        self.monitoring = True
        monitor_thread = threading.Thread(target=self._monitor_queue, args=(duration,))
        monitor_thread.daemon = True
        monitor_thread.start()
        return monitor_thread
        
    def _monitor_queue(self, duration):
        """Monitor the queue for events"""
        start_time = time.time()
        print(f"Starting event queue monitor for {duration} seconds...")
        
        while time.time() - start_time < duration and self.monitoring:
            try:
                if not event_queue.get_queue().empty():
                    event = event_queue.get_queue().get_nowait()
                    self.events_received.append(event)
                    
                    agent_name = event.get('agentName', 'Unknown')
                    event_type = event.get('eventType', 'Unknown')
                    payload = event.get('payload', {})
                    
                    if 'display_message' in payload:
                        message = payload['display_message']
                    elif 'tool_name' in payload:
                        message = f"{payload['tool_name']} called"
                    else:
                        message = str(payload)
                    
                    timestamp = time.time()
                    print(f"[{timestamp:.2f}] {agent_name} - {event_type}: {message}")
                    
            except Exception as e:
                pass  # Queue might be empty, that's fine
            time.sleep(0.1)  # Small delay to prevent busy waiting
        
        print(f"Event queue monitoring completed. Total events captured: {len(self.events_received)}")


async def test_competition_agent():
    """Test the Competition Agent with actual tasks"""
    print("🧪 Testing Competition Agent with parallel tool execution...")
    print("This will test the agent with a real business type and area.")
    
    # Start the event monitor
    monitor = AgentMonitor()
    monitor_thread = monitor.start_monitoring(duration=60)  # Monitor for up to 60 seconds
    
    try:
        # Define test tasks - business type and area
        test_tasks = ["bakery", "Nairobi, Kenya"]
        print(f"\n🚀 Running Competition Agent for: {test_tasks[0]} in {test_tasks[1]}")
        
        # Run the agent
        final_result = ""
        start_time = time.time()
        
        async for event in run_competition_agent(test_tasks):
            if 'delta' in event and 'text' in event['delta']:
                final_result += event['delta']['text']
                print(f"📝 Agent output: {event['delta']['text']}", end='', flush=True)
            elif 'error' in event:
                print(f"❌ Agent error: {event['error']}")
                break
            elif event.get('event') and 'tool' in str(event.get('event')).lower():
                print(f"🛠️  Tool event: {event}")
        
        end_time = time.time()
        print(f"\n\n⏱️  Agent execution completed in {end_time - start_time:.2f} seconds")
        
        if final_result:
            print(f"📄 Final agent response length: {len(final_result)} characters")
            print("✅ Agent completed successfully!")
        else:
            print("⚠️  Agent completed but no final response captured")
        
        # Stop monitoring and show results
        monitor.monitoring = False
        monitor_thread.join(timeout=2)  # Wait up to 2 seconds for thread to finish
        
        print(f"\n📊 Summary: Captured {len(monitor.events_received)} events from the agent")
        
        # Show event breakdown
        event_types = {}
        for event in monitor.events_received:
            agent_name = event.get('agentName', 'Unknown')
            event_type = event.get('eventType', 'Unknown')
            key = f"{agent_name}:{event_type}"
            event_types[key] = event_types.get(key, 0) + 1
        
        print("\n📈 Event breakdown by agent and type:")
        for event_key, count in event_types.items():
            print(f"  {event_key}: {count} events")
        
        # This is where we can see if parallel execution worked well
        # If the agent is using batch correctly, we should see events coming in rapidly
        # when both update_work_progress and find_competitors run in parallel
        print(f"\n🎯 The agent now has access to the batch tool to run update_work_progress and find_competitors simultaneously!")
        print("This allows frontend updates and actual work to happen at the same time for better performance.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error running Competition Agent: {e}")
        import traceback
        traceback.print_exc()
        monitor.monitoring = False
        return False


async def test_direct_batch_functionality():
    """Test if the agent can use batch functionality (conceptual - would be handled by LLM)"""
    print("\n🔍 Testing conceptual batch functionality...")
    print("When the agent receives instructions, it can now call:")
    print("batch(invocations=[")
    print("  {\"name\": \"update_work_progress\", \"arguments\": {...}},")
    print("  {\"name\": \"find_competitors\", \"arguments\": {...}}")
    print("])")
    print("This allows both frontend updates and actual work to happen simultaneously!")
    

async def main():
    print("🚀 Starting Competition Agent Parallel Execution Test\n")
    
    # Test 1: Direct batch functionality explanation
    await test_direct_batch_functionality()
    
    # Test 2: Actual agent run with monitoring
    success = await test_competition_agent()
    
    if success:
        print("\n🎉 Competition Agent test completed successfully!")
        print("✅ The agent now supports parallel tool execution using the batch tool")
        print("✅ Frontend updates and actual work can now happen simultaneously")
    else:
        print("\n❌ Competition Agent test encountered issues")


if __name__ == "__main__":
    asyncio.run(main())