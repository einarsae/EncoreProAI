#!/usr/bin/env python3
"""
Debug the order field issue in the full pipeline
"""

import asyncio
import os
import json
from workflow.graph import create_workflow
from models.state import AgentState, CoreState

TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"

async def debug_order_issue():
    """Debug the order field through the full pipeline"""
    
    # Create initial state
    initial_state = AgentState(
        core=CoreState(
            session_id="debug-order",
            user_id="test-user",
            tenant_id=TEST_TENANT_ID,
            query="Show me our top 5 shows by revenue"  # Simple query
        )
    )
    
    # Add user message
    initial_state.add_message("user", initial_state.core.query)
    
    # Create workflow
    workflow = create_workflow()
    
    print("Starting workflow execution...")
    print("=" * 80)
    
    # Track each step
    step_count = 0
    try:
        async for chunk in workflow.astream(initial_state, {"recursion_limit": 10}):
            step_count += 1
            node_name = list(chunk.keys())[0] if chunk else "unknown"
            print(f"\nStep {step_count}: {node_name}")
            
            # If it's the orchestrate node, show the decision
            if node_name == "orchestrate" and chunk.get("orchestrate"):
                state_dict = chunk["orchestrate"]
                # The state is returned as a dict, need to access core messages
                if "core" in state_dict and "messages" in state_dict["core"]:
                    messages = state_dict["core"]["messages"]
                    # Find the last system message with current_task
                    for msg in reversed(messages):
                        if msg.get("role") == "system" and "current_task" in msg.get("metadata", {}):
                            task = msg["metadata"]["current_task"]
                            print(f"  Task: {task}")
                            if "inputs" in task and "order" in task["inputs"]:
                                print(f"  Order field: {task['inputs']['order']}")
                                print(f"  Order type: {type(task['inputs']['order'])}")
                            break
            
            # If it's ticketing_data execution, check what happened
            if node_name == "execute_ticketing_data":
                state_dict = chunk["execute_ticketing_data"]
                if "core" in state_dict and "messages" in state_dict["core"]:
                    messages = state_dict["core"]["messages"]
                    # Check for errors in the last few messages
                    for msg in messages[-3:]:
                        if msg.get("role") == "system":
                            print(f"  System: {msg.get('content', '')[:200]}...")
                        
            # Stop after a few iterations to avoid spam
            if step_count > 10:
                print("\nStopping after 10 steps...")
                break
                
    except Exception as e:
        print(f"\nError during execution: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    print("Debugging Order Field Issue")
    print("=" * 80)
    print(f"Tenant: {TEST_TENANT_ID}")
    print("=" * 80)
    
    await debug_order_issue()

if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        exit(1)
    
    asyncio.run(main())