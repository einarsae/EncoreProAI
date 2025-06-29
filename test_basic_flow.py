"""
Basic test to verify orchestration flow works

Simpler test without complex date ranges or analysis.
"""

import asyncio
import os
from datetime import datetime

from workflow.graph import create_workflow
from models.state import AgentState, CoreState, DebugState


async def test_basic_flow():
    """Test basic flow through the orchestration"""
    
    workflow = create_workflow()
    
    # Very simple query
    initial_state = AgentState(
        core=CoreState(
            session_id="test_basic",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
            user_id="user123",
            query="Show me total revenue",
            timestamp=datetime.utcnow()
        ),
        debug=DebugState(trace_enabled=True)
    )
    
    print("Query:", initial_state.core.query)
    print("\nProcessing...")
    
    # Track nodes visited
    nodes_visited = []
    iterations = 0
    max_iterations = 20  # Safety limit
    
    try:
        async for state_update in workflow.astream(initial_state):
            iterations += 1
            
            # Extract node name and state
            for node_name, state in state_update.items():
                nodes_visited.append(node_name)
                print(f"\nIteration {iterations}: {node_name}")
                
                if hasattr(state, 'routing'):
                    print(f"  Next node: {state.routing.next_node}")
                
                if hasattr(state, 'execution') and state.execution.completed_tasks:
                    print(f"  Completed tasks: {len(state.execution.completed_tasks)}")
                    for task_id, task in state.execution.completed_tasks.items():
                        print(f"    - {task_id}: {task.capability} (success={task.success})")
                
                if hasattr(state, 'core'):
                    print(f"  Status: {state.core.status}")
                    if state.core.status == "complete":
                        print("  ✓ Workflow completed!")
                        print(f"  Final response: {state.core.final_response}")
                        return
            
            if iterations >= max_iterations:
                print(f"\n⚠️  Hit max iterations ({max_iterations})")
                break
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nNodes visited: {' → '.join(nodes_visited)}")
    print(f"Total iterations: {iterations}")


async def test_with_timeout():
    """Test with timeout to prevent hanging"""
    try:
        await asyncio.wait_for(test_basic_flow(), timeout=30.0)
    except asyncio.TimeoutError:
        print("\n⏱️  Test timed out after 30 seconds")


if __name__ == "__main__":
    print("Starting basic flow test...")
    print(f"Tenant ID: {os.getenv('DEFAULT_TENANT_ID')}")
    asyncio.run(test_with_timeout())