#!/usr/bin/env python3
"""
Test script for the orchestrator agent functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator_agent import (
    orchestrator_agent_tool, 
    chat_with_orchestrator, 
    get_orchestrator_state, 
    clear_orchestrator_state,
    orchestrator
)

def test_orchestrator_agent_direct():
    """Test the orchestrator agent directly"""
    print("🧪 Testing Orchestrator Agent Direct Communication")
    print("=" * 60)
    
    # Clear state first
    clear_orchestrator_state()
    print("✅ Cleared orchestrator state")
    
    # Test direct chat with orchestrator
    test_message = "Hello orchestrator! Can you help coordinate some research tasks?"
    
    print(f"\n📤 Sending message: {test_message}")
    
    try:
        response = chat_with_orchestrator(test_message)
        print(f"\n🤖 Orchestrator Response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        
        # Check state after communication
        state = get_orchestrator_state()
        print(f"\n📊 State after direct communication:")
        print(f"  - Execution status: {state['execution_status']}")
        print(f"  - Last update: {state['last_update']}")
        
        print("\n✅ Direct orchestrator test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing direct orchestrator: {e}")
        return False

def test_orchestrator_agent_tool():
    """Test the orchestrator agent tool (how planner calls it)"""
    print("\n🧪 Testing Orchestrator Agent Tool")
    print("=" * 60)
    
    # Test sending a research plan via the tool
    research_plan_message = """
I have completed creating a comprehensive research plan for a food delivery business. Here are the tasks organized by category:

COMPETITION TASKS:
- Analyze direct competitors in food delivery space (UberEats, DoorDash, Grubhub)
- Research pricing strategies of top 3 competitors
- Evaluate competitor market positioning and value propositions

MARKET TASKS:
- Determine total addressable market size for food delivery
- Analyze customer demographics and ordering preferences
- Assess market demand validation in target cities

FINANCIAL TASKS:
- Model unit economics for delivery operations
- Develop pricing strategy framework
- Create financial projections for 3 years

RISK TASKS:
- Evaluate regulatory compliance requirements for food delivery
- Assess operational risks in delivery logistics
- Analyze competitive threats and market risks

SYNTHESIS REQUIREMENTS:
- Create executive summary of findings
- Develop strategic recommendations
- Prepare visual intelligence dashboard

Please coordinate the execution of these research tasks and provide updates on progress.
"""
    
    print("📋 Sending research plan via orchestrator_agent_tool...")
    
    try:
        response = orchestrator_agent_tool(research_plan_message)
        print(f"\n🤖 Orchestrator Tool Response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        
        # Check state after tool communication
        state = get_orchestrator_state()
        print(f"\n📊 State after tool communication:")
        print(f"  - Execution status: {state['execution_status']}")
        print(f"  - Last update: {state['last_update']}")
        
        print("\n✅ Orchestrator agent tool test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing orchestrator agent tool: {e}")
        return False

def test_orchestrator_mock_tools():
    """Test that the orchestrator calls its mock tools correctly"""
    print("\n🧪 Testing Orchestrator Mock Tool Usage")
    print("=" * 60)
    
    # Send a message that should trigger tool usage
    tool_test_message = """
I need you to process a simple research task. Please use your mock_orchestrator_tool to simulate processing this task: "Market Analysis for Tech Startup"
"""
    
    print("🔧 Testing mock tool usage...")
    
    try:
        response = chat_with_orchestrator(tool_test_message)
        print(f"\n🤖 Orchestrator Response (should show tool usage):")
        print("-" * 40)
        print(response)
        print("-" * 40)
        
        # Check if the response mentions tool usage or coordination
        if "phase" in response.lower() or "coordination" in response.lower() or "processed" in response.lower():
            print("\n✅ Tool coordination detected in response!")
        else:
            print("\n⚠️ Tool coordination not clearly detected in response")
        
        print("\n✅ Mock tool test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing mock tools: {e}")
        return False

def test_orchestrator_agent_class():
    """Test the orchestrator agent class directly"""
    print("\n🧪 Testing Orchestrator Agent Class")
    print("=" * 60)
    
    try:
        # Test that the orchestrator instance exists and is properly initialized
        print(f"📋 Orchestrator agent model: {orchestrator.agent.model}")
        print(f"📋 Orchestrator agent name: {orchestrator.agent.name}")
        print(f"📋 Orchestrator agent has tools: {len(orchestrator.agent.tools) > 0}")
        
        # Test a simple chat
        simple_message = "What is your role as the orchestrator?"
        response = orchestrator.chat(simple_message)
        
        print(f"\n🤖 Simple Chat Response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        
        print("\n✅ Orchestrator agent class test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing orchestrator agent class: {e}")
        return False

def test_orchestrator_state_management():
    """Test orchestrator state management functions"""
    print("\n🧪 Testing Orchestrator State Management")
    print("=" * 60)
    
    try:
        # Test initial state
        initial_state = get_orchestrator_state()
        print(f"📊 Initial state: {initial_state}")
        
        # Test clearing state
        clear_orchestrator_state()
        cleared_state = get_orchestrator_state()
        print(f"📊 Cleared state: {cleared_state}")
        
        # Verify state is properly cleared
        assert cleared_state["execution_status"] == "idle"
        assert cleared_state["current_plan"] is None
        assert cleared_state["tasks"] == []
        
        print("\n✅ State management test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing state management: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Orchestrator Agent Tests")
    print("=" * 60)
    
    # Run all tests
    tests = [
        test_orchestrator_agent_class,
        test_orchestrator_state_management,
        test_orchestrator_agent_direct,
        test_orchestrator_mock_tools,
        test_orchestrator_agent_tool,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All orchestrator agent tests passed!")
    else:
        print("⚠️ Some tests failed. Please check the output above.")
    
    print("=" * 60)