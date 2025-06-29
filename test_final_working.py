"""
Test orchestration completion with proper state tracking
"""

import asyncio
import os
from datetime import datetime

from workflow.graph import create_workflow, process_query


async def test_with_process_query():
    """Test using the process_query helper that handles state properly"""
    
    print("Testing with process_query helper...")
    
    result = await process_query(
        query="Show me total revenue",
        session_id="test_final",
        user_id="user123",
        tenant_id=os.getenv("DEFAULT_TENANT_ID"),
        debug=True
    )
    
    print(f"\nSuccess: {result['success']}")
    print(f"Response: {result.get('response', {})}")
    
    return result


async def test_manual_workflow():
    """Test with manual workflow tracking"""
    
    print("\n\nTesting with manual workflow...")
    
    workflow = create_workflow()
    
    from models.state import AgentState, CoreState
    initial_state = AgentState(
        core=CoreState(
            session_id="test_manual",
            tenant_id=os.getenv("DEFAULT_TENANT_ID"),
            user_id="user123",
            query="What is the total revenue for November 2024?",
            timestamp=datetime.utcnow()
        )
    )
    
    # The workflow maintains state internally
    # We need to run it to completion
    final_state = None
    nodes_visited = []
    
    async for chunk in workflow.astream(initial_state, {"recursion_limit": 15}):
        for node, _ in chunk.items():
            nodes_visited.append(node)
            print(f"  -> {node}")
    
    # Get the final state using ainvoke instead
    print("\nRunning with ainvoke for final state...")
    final_state = await workflow.ainvoke(initial_state, {"recursion_limit": 15})
    
    print(f"\nNodes visited: {' → '.join(nodes_visited)}")
    print(f"Final status: {final_state.core.status}")
    print(f"Final response: {final_state.core.final_response}")
    
    return final_state


if __name__ == "__main__":
    # Test 1: Using helper
    asyncio.run(test_with_process_query())
    
    # Test 2: Manual workflow
    asyncio.run(test_manual_workflow())