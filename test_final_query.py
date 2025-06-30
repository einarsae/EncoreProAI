#!/usr/bin/env python3
"""
Test query using the correct method (ainvoke)
"""

import asyncio
import os
import logging
from workflow.graph import create_workflow, process_query
from models.state import AgentState

# Minimal logging
logging.basicConfig(level=logging.ERROR)

async def test_with_ainvoke():
    """Test using ainvoke to get final state"""
    
    query = "What is the total revenue for Gatsby?"
    print(f"\nTesting: {query}")
    
    # Method 1: Use process_query helper
    result = await process_query(
        query=query,
        session_id="test_final",
        user_id="test_user",
        tenant_id=os.getenv("TENANT_ID", "yesplan"),
        debug=False
    )
    
    print(f"\nResult from process_query:")
    print(f"  Success: {result['success']}")
    if result['response']:
        print(f"  Response: {result['response'].get('message', 'No message')}")
    else:
        print(f"  Response: None")
    
    # Method 2: Use workflow.ainvoke directly
    print(f"\n{'='*60}")
    print("Testing with direct ainvoke:")
    
    workflow = create_workflow()
    initial_state = AgentState(
        core={
            "session_id": "test_direct",
            "user_id": "test_user",
            "tenant_id": os.getenv("TENANT_ID", "yesplan"),
            "query": query
        }
    )
    
    final_state = await workflow.ainvoke(initial_state, {"recursion_limit": 15})
    
    if isinstance(final_state, dict) and 'core' in final_state:
        core = final_state['core']
        print(f"  Status: {core.status}")
        if hasattr(core, 'final_response') and core.final_response:
            print(f"  Response: {core.final_response.message}")
        else:
            print(f"  No final response found")
    else:
        print(f"  Unexpected result type: {type(final_state)}")


async def test_multiple_queries():
    """Test multiple queries"""
    queries = [
        "What is the total revenue for Gatsby?",
        "How many tickets were sold for Hell's Kitchen?",
        "Compare sales for Hell's Kitchen and Chicago"
    ]
    
    print("\nTesting multiple queries:")
    print("="*60)
    
    for query in queries:
        result = await process_query(
            query=query,
            session_id="test_multi",
            user_id="test_user",
            tenant_id=os.getenv("TENANT_ID", "yesplan"),
            debug=False
        )
        
        print(f"\nQuery: {query}")
        print(f"Success: {result['success']}")
        if result['response']:
            print(f"Response: {result['response'].get('message', 'No message')[:100]}...")


if __name__ == "__main__":
    asyncio.run(test_with_ainvoke())
    print("\n" + "="*80 + "\n")
    asyncio.run(test_multiple_queries())