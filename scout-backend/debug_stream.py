#!/usr/bin/env python3
"""
Debug the streaming function locally
"""

import asyncio
import logging
from agents.planner_agent import chat_with_planner_streaming

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_streaming():
    print("Testing streaming function...")
    
    try:
        count = 0
        async for chunk in chat_with_planner_streaming("hello"):
            count += 1
            print(f"Chunk {count}: {chunk}")
            
        print(f"Total chunks received: {count}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming())