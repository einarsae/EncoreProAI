"""
Test orchestration with explicit date handling
"""

import asyncio
import os
from datetime import datetime

from workflow.graph import create_workflow
from models.state import AgentState, CoreState, DebugState


async def test_with_explicit_dates():
    """Test query that should work with date conversion"""
    
    workflow = create_workflow()
    
    # Query with relative date that should be converted
    initial_state = AgentState(
        core=CoreState(
            session_id="test_dates",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
            user_id="user123",
            query="Show me revenue for last month",
            timestamp=datetime.utcnow()
        ),
        debug=DebugState(trace_enabled=True)
    )
    
    print(f"Query: {initial_state.core.query}")
    print(f"Today's date: {datetime.now().strftime('%Y-%m-%d')}")
    print("\nProcessing...")
    
    nodes_visited = []
    final_state = None
    
    try:
        async for state_update in workflow.astream(initial_state):
            for node_name, state in state_update.items():
                nodes_visited.append(node_name)
                print(f"\n{node_name}:")
                
                if hasattr(state, 'routing'):
                    print(f"  Next: {state.routing.next_node}")
                
                if hasattr(state, 'execution') and state.execution.completed_tasks:
                    for task_id, task in state.execution.completed_tasks.items():
                        print(f"  Task {task_id}: {task.capability} (success={task.success})")
                        if task.success and "data" in task.result:
                            print(f"    Data points: {len(task.result['data'])}")
                        if task.error_message:
                            print(f"    Error: {task.error_message}")
                
                if hasattr(state, 'core') and state.core.status == "complete":
                    print("  ✓ Workflow completed!")
                    final_state = state
                    return final_state
                    
        print(f"\nNodes visited: {' → '.join(nodes_visited)}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    return final_state


async def main():
    print("Testing date conversion in orchestration...")
    print(f"Tenant ID: {os.getenv('DEFAULT_TENANT_ID')}")
    
    state = await test_with_explicit_dates()
    
    if state and hasattr(state, 'core'):
        print(f"\nFinal status: {state.core.status}")
        if state.core.final_response:
            print(f"Response: {state.core.final_response}")


if __name__ == "__main__":
    asyncio.run(main())