"""
Debug task execution
"""

import asyncio
import os
from datetime import datetime

from workflow.nodes import WorkflowNodes
from models.state import AgentState, CoreState, ExecutionState
from models.frame import Frame


async def test_task_execution():
    """Debug task execution step by step"""
    
    nodes = WorkflowNodes()
    
    # Create initial state
    state = AgentState(
        core=CoreState(
            session_id="test_task",
            tenant_id=os.getenv("DEFAULT_TENANT_ID"),
            user_id="user123",
            query="What is the total revenue?",
            timestamp=datetime.utcnow()
        ),
        execution=ExecutionState()
    )
    
    # Simulate frame extraction
    state.semantic.frames = [Frame(
        id="0",
        query="What is the total revenue?",
        entities=[],
        concepts=["revenue", "total"]
    )]
    state.semantic.current_frame_id = "0"
    
    # Simulate orchestration decision
    state.add_message("system", "Executing task t1: ticketing_data", 
                     metadata={"current_task": {
                         "id": "t1",
                         "capability": "ticketing_data",
                         "inputs": {
                             "query_request": "total revenue",
                             "measures": ["revenue"]
                         }
                     }})
    
    print("Executing ticketing_data task...")
    state = await nodes.execute_ticketing_data_node(state)
    
    print(f"\nAfter execution:")
    print(f"  Next node: {state.routing.next_node}")
    print(f"  Completed tasks: {len(state.execution.completed_tasks)}")
    
    if state.execution.completed_tasks:
        task = list(state.execution.completed_tasks.values())[0]
        print(f"  Task success: {task.success}")
        if task.result:
            print(f"  Result keys: {list(task.result.keys())}")
            if "data" in task.result:
                print(f"  Data points: {len(task.result['data'])}")
        if task.error_message:
            print(f"  Error: {task.error_message}")
    
    # Now run orchestration to see decision
    print("\nRunning orchestration...")
    state = await nodes.orchestrate_node(state)
    
    print(f"\nAfter orchestration:")
    print(f"  Status: {state.core.status}")
    print(f"  Next node: {state.routing.next_node}")
    if state.core.final_response:
        print(f"  Final response: {state.core.final_response}")


if __name__ == "__main__":
    asyncio.run(test_task_execution())