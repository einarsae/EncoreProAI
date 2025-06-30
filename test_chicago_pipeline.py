"""
Test Chicago pipeline to debug final state retrieval
"""

import asyncio
import os
from datetime import datetime

from workflow.graph import create_workflow, process_query
from models.state import AgentState, CoreState, DebugState


async def test_chicago_direct():
    """Test the query directly with the workflow"""
    
    workflow = create_workflow()
    
    initial_state = AgentState(
        core=CoreState(
            session_id="test_chicago",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
            user_id="user123",
            query="What is the total revenue for Chicago?"
        ),
        debug=DebugState(trace_enabled=True)
    )
    
    # Add user message
    initial_state.add_message("user", initial_state.core.query)
    
    print(f"Query: {initial_state.core.query}")
    print("\nProcessing with astream to see all nodes...")
    
    # First let's see what nodes are executed
    nodes = []
    final_state = None
    
    async for state_update in workflow.astream(initial_state, {"recursion_limit": 15}):
        node_name = list(state_update.keys())[0] if state_update else "unknown"
        nodes.append(node_name)
        print(f"  - {node_name}")
        
        # Keep the last state update (before __end__)
        if node_name != '__end__':
            final_state = state_update.get(node_name)
    
    print(f"\nNodes executed: {' → '.join(nodes)}")
    
    # Now test with ainvoke
    print("\n\nTesting with ainvoke...")
    initial_state2 = AgentState(
        core=CoreState(
            session_id="test_chicago2",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
            user_id="user123",
            query="What is the total revenue for Chicago?"
        )
    )
    initial_state2.add_message("user", initial_state2.core.query)
    
    result = await workflow.ainvoke(initial_state2, {"recursion_limit": 15})
    
    print("\nResult type:", type(result))
    print("Result keys:", list(result.keys()) if isinstance(result, dict) else "Not a dict")
    
    if isinstance(result, dict):
        # Check what's in the result
        for key, value in result.items():
            print(f"\n{key}:")
            if hasattr(value, '__dict__'):
                print(f"  Type: {type(value)}")
                if hasattr(value, 'status'):
                    print(f"  Status: {value.status}")
                if hasattr(value, 'final_response'):
                    print(f"  Final Response: {value.final_response}")
            else:
                print(f"  Value: {value}")
    
    # Finally test with process_query
    print("\n\nTesting with process_query...")
    result = await process_query(
        query="What is the total revenue for Chicago?",
        session_id="test_chicago3",
        user_id="user123",
        tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
        debug=True
    )
    
    print("\nProcess Query Result:")
    print(f"Success: {result.get('success')}")
    print(f"Response: {result.get('response')}")
    print(f"Error: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(test_chicago_direct())