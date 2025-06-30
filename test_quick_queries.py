#!/usr/bin/env python3
"""
Quick test of a few queries with timeouts
"""

import asyncio
import os
import logging
from workflow.graph import create_workflow
from models.state import AgentState

# Minimal logging
logging.basicConfig(level=logging.ERROR)

# Just test a few queries
TEST_QUERIES = [
    "What is the total revenue for Gatsby?",
    "Compare sales for Hell's Kitchen and Chicago",
    "I'm feeling overwhelmed with all these numbers"
]


async def test_query_with_timeout(query: str, timeout: int = 30):
    """Test a single query with timeout"""
    print(f"\nTesting: {query}")
    
    try:
        # Create task with timeout
        async def run_query():
            app = create_workflow()
            initial_state = AgentState(
                core={
                    "session_id": "quick_test",
                    "user_id": "test_user",
                    "tenant_id": os.getenv("TENANT_ID", "yesplan"),
                    "query": query
                }
            )
            
            steps = 0
            final_response = None
            
            async for event in app.astream(initial_state):
                steps += 1
                for node, state in event.items():
                    if hasattr(state, 'core') and state.core.final_response:
                        final_response = state.core.final_response
                        
                # Max 10 steps
                if steps >= 10:
                    print(f"❌ Too many steps ({steps})")
                    return None
                        
            return final_response
        
        # Run with timeout
        result = await asyncio.wait_for(run_query(), timeout=timeout)
        
        if result:
            print(f"✅ SUCCESS")
            if hasattr(result, 'message'):
                print(f"   Response: {result.message[:100]}...")
            else:
                # Try to get the actual response
                response_text = str(result)
                if len(response_text) > 100:
                    print(f"   Response: {response_text[:100]}...")
                else:
                    print(f"   Response: {response_text}")
        else:
            print(f"❌ No response")
            
    except asyncio.TimeoutError:
        print(f"❌ TIMEOUT after {timeout}s")
    except Exception as e:
        print(f"❌ ERROR: {str(e)[:100]}")


async def main():
    """Run quick tests"""
    print("Running quick tests...")
    
    for query in TEST_QUERIES:
        await test_query_with_timeout(query, timeout=30)
    
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())