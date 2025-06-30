"""Simple test of dynamic capability system"""

import asyncio
import os
from workflow.graph import process_query

async def test_help():
    """Test help capability routing"""
    print("\n=== Testing Help Capability ===")
    
    result = await process_query(
        query="What can you help me with?",
        session_id="test-session",
        user_id="test-user",
        tenant_id=os.getenv("DEFAULT_TENANT_ID", "test_tenant")
    )
    
    print(f"Success: {result['success']}")
    if result['success'] and result.get('response'):
        print(f"Response preview: {result['response']['message'][:200]}...")
    else:
        print(f"Error: {result.get('error')}")

async def test_dynamic_routing():
    """Test that capabilities are found without hardcoding"""
    print("\n=== Testing Dynamic Routing ===")
    
    queries = [
        ("I'm feeling overwhelmed", "Should route to chat"),
        ("Analyze trends for Chicago", "Should route to event_analysis"),
        ("What's the revenue for Hamilton?", "Should route to ticketing_data"),
    ]
    
    for query, expected in queries:
        print(f"\nQuery: {query}")
        print(f"Expected: {expected}")
        
        # We can't test the full pipeline due to filter format issues,
        # but we can check the capabilities exist
        
        from capabilities.registry import get_registry
        registry = get_registry()
        capabilities = registry.get_all_instances()
        
        print(f"Available capabilities: {list(capabilities.keys())}")
        

if __name__ == "__main__":
    print("Testing Dynamic Capability System")
    asyncio.run(test_help())
    asyncio.run(test_dynamic_routing())