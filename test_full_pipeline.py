"""
Test the full orchestration pipeline using the workflow graph

This runs complete end-to-end tests with the LangGraph workflow.
"""

import asyncio
import os
from datetime import datetime

from workflow.graph import create_workflow, process_query
from models.state import AgentState, CoreState


async def test_with_graph():
    """Test using the workflow graph directly"""
    print("\n=== Testing with Workflow Graph ===")
    
    # Test 1: Simple revenue query
    print("\nTest 1: Simple Revenue Query")
    result = await process_query(
        query="Show me total revenue for all productions",
        session_id="test_graph_1",
        user_id="user123",
        tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
        debug=True
    )
    print(f"Success: {result['success']}")
    if result['response']:
        print(f"Response: {result['response']}")
    
    # Test 2: Entity-specific query
    print("\n\nTest 2: Entity Query (Chicago)")
    result = await process_query(
        query="How much revenue did Chicago generate last month?",
        session_id="test_graph_2",
        user_id="user123",
        tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
        debug=True
    )
    print(f"Success: {result['success']}")
    
    # Test 3: Analysis query
    print("\n\nTest 3: Analysis Query")
    result = await process_query(
        query="Analyze the performance trends for Chicago over the last 3 months",
        session_id="test_graph_3",
        user_id="user123",
        tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
        debug=True
    )
    print(f"Success: {result['success']}")
    
    # Test 4: Comparison query
    print("\n\nTest 4: Comparison Query")
    result = await process_query(
        query="Compare revenue between Chicago and Hamilton",
        session_id="test_graph_4",
        user_id="user123",
        tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
        debug=True
    )
    print(f"Success: {result['success']}")


async def test_graph_states():
    """Test the graph with direct state inspection"""
    print("\n=== Testing Graph State Flow ===")
    
    workflow = create_workflow()
    
    initial_state = AgentState(
        core=CoreState(
            session_id="test_states",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
            user_id="user123",
            query="Show revenue for Chicago by month",
            timestamp=datetime.utcnow()
        )
    )
    
    print("Initial query:", initial_state.core.query)
    print("\nProcessing through workflow...")
    
    # Track state changes
    states = []
    async for state_update in workflow.astream(initial_state):
        # The update is a dict with node name as key
        for node_name, state in state_update.items():
            print(f"\nNode: {node_name}")
            if hasattr(state, 'routing'):
                print(f"  Next: {state.routing.next_node}")
            if hasattr(state, 'execution') and state.execution.completed_tasks:
                print(f"  Tasks: {len(state.execution.completed_tasks)}")
            if hasattr(state, 'semantic') and state.semantic.frames:
                print(f"  Frames: {len(state.semantic.frames)}")
            states.append((node_name, state))
    
    # Final state
    final_state = states[-1][1] if states else None
    if final_state and hasattr(final_state, 'core'):
        print(f"\nFinal status: {final_state.core.status}")
        print(f"Completed tasks: {len(final_state.execution.completed_tasks)}")
        
        # Show task results
        for task_id, task in final_state.execution.completed_tasks.items():
            print(f"\n{task_id}: {task.capability}")
            print(f"  Success: {task.success}")
            if task.error_message:
                print(f"  Error: {task.error_message}")
            elif task.result and "data" in task.result:
                print(f"  Data points: {len(task.result['data'])}")


async def main():
    """Run all tests"""
    print("Starting full pipeline tests...")
    print(f"Tenant ID: {os.getenv('DEFAULT_TENANT_ID')}")
    
    try:
        # Test with process_query helper
        await test_with_graph()
        
        # Test with direct graph inspection
        await test_graph_states()
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())