#!/usr/bin/env python3
"""
Test a subset of queries to verify system functionality
"""

import asyncio
import os
import logging
from workflow.graph import create_workflow
from models.state import AgentState

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Less verbose for testing
logger = logging.getLogger(__name__)

# Small subset of test queries
TEST_QUERIES = [
    # Simple data
    "What is the total revenue for Gatsby?",
    "How many tickets were sold for Hell's Kitchen?",
    
    # Time-based
    "What were last month's sales?",
    
    # Comparison
    "Compare sales for Hell's Kitchen and Chicago",
    
    # Trend
    "Is Hell's Kitchen revenue declining?",
    
    # Analysis
    "Which shows need attention?",
    
    # Emotional support
    "I'm feeling overwhelmed with all these numbers",
    
    # Ambiguous
    "How are we doing?"
]


async def test_query(query: str):
    """Test a single query"""
    print(f"\nTesting: {query}")
    
    try:
        # Create workflow
        app = create_workflow()
        
        # Create initial state
        initial_state = AgentState(
            core={
                "session_id": "test_subset",
                "user_id": "test_user",
                "tenant_id": os.getenv("TENANT_ID", "yesplan"),
                "query": query
            }
        )
        
        # Track execution
        steps = 0
        final_response = None
        capabilities_used = []
        
        # Run workflow
        async for event in app.astream(initial_state):
            for node, state in event.items():
                steps += 1
                
                if hasattr(state, 'routing') and state.routing.capability_to_execute:
                    capabilities_used.append(state.routing.capability_to_execute)
                
                if hasattr(state, 'core') and state.core.final_response:
                    final_response = state.core.final_response
        
        # Print results
        if final_response:
            print(f"✅ SUCCESS in {steps} steps")
            print(f"   Capabilities: {', '.join(capabilities_used) if capabilities_used else 'none'}")
            if hasattr(final_response, 'message'):
                print(f"   Response: {final_response.message[:100]}...")
            else:
                print(f"   Response: {str(final_response)[:100]}...")
        else:
            print(f"❌ FAILED after {steps} steps")
        
        return final_response is not None
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


async def main():
    """Test all queries"""
    print(f"Testing {len(TEST_QUERIES)} queries...\n")
    
    results = []
    for query in TEST_QUERIES:
        success = await test_query(query)
        results.append(success)
        await asyncio.sleep(0.5)  # Small delay between queries
    
    # Summary
    successful = sum(results)
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {successful}/{total} queries successful ({successful/total*100:.0f}%)")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())