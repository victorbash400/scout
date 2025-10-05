#!/usr/bin/env python3
"""
Test planner agent functionality
"""

import asyncio
from agents.planner_agent import planner

async def test_planner():
    print("Testing planner agent...")
    
    # Test regular chat
    print("\n=== Testing regular chat ===")
    try:
        response = planner.chat("hello")
        print(f"Regular chat response: {response}")
    except Exception as e:
        print(f"Regular chat failed: {e}")
    
    # Test streaming chat
    print("\n=== Testing streaming chat ===")
    try:
        count = 0
        async for chunk in planner.chat_streaming("hello"):
            count += 1
            print(f"Stream chunk {count}: {chunk}")
        print(f"Total streaming chunks: {count}")
    except Exception as e:
        print(f"Streaming chat failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_planner())