#!/usr/bin/env python3
"""
Debug the infinite loop issue with direct logging
"""

import asyncio
import os
import logging
from workflow.graph import create_workflow
from models.state import AgentState

# Configure logging to see everything
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s'
)

async def debug_simple_query():
    """Debug a simple query step by step"""
    
    # Create workflow
    app = create_workflow()
    
    # Create initial state
    initial_state = AgentState(
        core={
            "session_id": "debug_session",
            "user_id": "test_user", 
            "tenant_id": os.getenv("TENANT_ID", "yesplan"),
            "query": "What is the total revenue for Gatsby?"
        }
    )
    
    print("\n=== STARTING WORKFLOW ===")
    print(f"Query: {initial_state.core.query}")
    
    # Track steps
    step_count = 0
    max_steps = 10
    
    # Run workflow step by step
    async for event in app.astream(initial_state):
        step_count += 1
        print(f"\n--- Step {step_count} ---")
        
        # Show what happened
        for node, state in event.items():
            print(f"Node: {node}")
            
            # Show routing decision
            if hasattr(state, 'routing'):
                print(f"  Next node: {state.routing.next_node}")
                if state.routing.capability_to_execute:
                    print(f"  Capability to execute: {state.routing.capability_to_execute}")
            
            # Show completed tasks
            if hasattr(state, 'execution'):
                print(f"  Completed tasks: {list(state.execution.completed_tasks.keys())}")
                print(f"  Loop count: {state.execution.loop_count}")
            
            # Show messages
            if hasattr(state, 'core') and state.core.messages:
                last_msg = state.core.messages[-1]
                print(f"  Last message: {last_msg.role} - {last_msg.content[:100]}...")
        
        # Safety check
        if step_count >= max_steps:
            print(f"\n❌ Stopping after {max_steps} steps - infinite loop detected!")
            break
    
    print("\n=== WORKFLOW COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(debug_simple_query())