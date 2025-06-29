"""
Debug orchestrator decisions
"""

import asyncio
import os
from datetime import datetime

from workflow.nodes import WorkflowNodes
from models.state import AgentState, CoreState, ExecutionState, TaskResult


async def test_orchestrator_logic():
    """Test orchestrator decision making directly"""
    
    nodes = WorkflowNodes()
    
    # Create state with completed ticketing_data task
    state = AgentState(
        core=CoreState(
            session_id="test_debug",
            tenant_id=os.getenv("DEFAULT_TENANT_ID"),
            user_id="user123",
            query="Show me total revenue",
            timestamp=datetime.utcnow()
        ),
        execution=ExecutionState()
    )
    
    # Add a successful task result
    task_result = TaskResult(
        task_id="t1",
        capability="ticketing_data",
        inputs={"measures": ["ticket_line_items.amount"]},
        result={
            "data": [
                {"ticket_line_items.amount": 1234567.89}
            ],
            "success": True,
            "total_count": 1
        },
        success=True
    )
    state.execution.add_task_result(task_result)
    
    print("Initial state:")
    print(f"  Query: {state.core.query}")
    print(f"  Completed tasks: {list(state.execution.completed_tasks.keys())}")
    print(f"  Status: {state.core.status}")
    
    # Build orchestration context
    context = nodes._build_orchestration_context(state)
    print("\nOrchestration context preview:")
    print(context[:500] + "...")
    
    # Get orchestration decision
    print("\nGetting orchestration decision...")
    decision = await nodes._get_orchestration_decision(context)
    print(f"\nDecision: {decision}")
    
    # Apply decision
    if decision["action"] == "complete":
        state.core.status = "complete"
        state.core.final_response = decision.get("response", {})
        state.routing.next_node = "end"
    else:
        state.routing.next_node = f"execute_{decision['capability']}"
    
    print(f"\nFinal state:")
    print(f"  Status: {state.core.status}")
    print(f"  Next node: {state.routing.next_node}")


if __name__ == "__main__":
    asyncio.run(test_orchestrator_logic())