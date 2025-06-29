"""
Working orchestration test that properly handles LangGraph streaming
"""

import asyncio
import os
from datetime import datetime

from workflow.graph import create_workflow, process_query
from models.state import AgentState, CoreState


async def test_simple_query():
    """Test simple query using process_query helper"""
    print("=== Test 1: Using process_query helper ===")
    
    result = await process_query(
        query="What is the total revenue?",
        session_id="test1",
        user_id="user123", 
        tenant_id=os.getenv("DEFAULT_TENANT_ID"),
        debug=False
    )
    
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Response: {result['response']}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    return result


async def test_date_query():
    """Test query with date that needs conversion"""
    print("\n\n=== Test 2: Query with relative date ===")
    
    result = await process_query(
        query="Show me revenue for last month by production",
        session_id="test2",
        user_id="user123",
        tenant_id=os.getenv("DEFAULT_TENANT_ID"),
        debug=False
    )
    
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Response: {result['response']}")
    
    return result


async def test_analysis_query():
    """Test analysis query requiring multiple steps"""
    print("\n\n=== Test 3: Analysis query ===")
    
    result = await process_query(
        query="Analyze revenue trends for Chicago",
        session_id="test3",
        user_id="user123",
        tenant_id=os.getenv("DEFAULT_TENANT_ID"),
        debug=False
    )
    
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Response: {result['response']}")
    
    return result


async def test_manual_workflow():
    """Test using workflow directly with proper completion detection"""
    print("\n\n=== Test 4: Manual workflow with streaming ===")
    
    workflow = create_workflow()
    
    initial_state = AgentState(
        core=CoreState(
            session_id="test_manual",
            tenant_id=os.getenv("DEFAULT_TENANT_ID"),
            user_id="user123",
            query="Total revenue for all productions",
            timestamp=datetime.utcnow()
        )
    )
    
    print(f"Query: {initial_state.core.query}")
    
    # Option 1: Just use ainvoke for the final result
    print("\nRunning with ainvoke...")
    final_dict = await workflow.ainvoke(initial_state, {"recursion_limit": 15})
    
    # Extract state components
    core = final_dict['core']
    print(f"\nFinal status: {core.status}")
    print(f"Final response: {core.final_response}")
    
    # Option 2: Stream to watch progress
    print("\n\nRunning same query with streaming to see progress...")
    nodes = []
    async for chunk in workflow.astream(initial_state, {"recursion_limit": 15}):
        node_name = list(chunk.keys())[0]
        nodes.append(node_name)
        print(f"  -> {node_name}")
    
    print(f"\nPath: {' → '.join(nodes)}")
    
    return final_dict


async def main():
    """Run all tests"""
    print("Starting orchestration tests...")
    print(f"Tenant ID: {os.getenv('DEFAULT_TENANT_ID')}")
    print(f"Today's date: {datetime.now().strftime('%Y-%m-%d')}")
    
    # Run tests
    await test_simple_query()
    await test_date_query()
    await test_analysis_query()
    await test_manual_workflow()
    
    print("\n\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())