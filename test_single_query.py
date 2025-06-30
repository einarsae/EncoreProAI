#!/usr/bin/env python3
"""
Test a single query with detailed output
"""

import asyncio
import os
import logging
from workflow.graph import create_workflow
from models.state import AgentState

# Enable info logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(message)s')

async def test_single_query():
    """Test one query with full details"""
    
    query = "What is the total revenue for Gatsby?"
    print(f"\n{'='*60}")
    print(f"Testing: {query}")
    print(f"{'='*60}\n")
    
    # Create workflow
    app = create_workflow()
    
    # Create initial state
    initial_state = AgentState(
        core={
            "session_id": "test_single",
            "user_id": "test_user",
            "tenant_id": os.getenv("TENANT_ID", "yesplan"),
            "query": query
        }
    )
    
    # Track execution
    steps = 0
    final_state = None
    
    # Run workflow
    async for event in app.astream(initial_state):
        steps += 1
        print(f"\nStep {steps}:")
        
        for node, state in event.items():
            print(f"  Node: {node}")
            
            # Save final state
            final_state = state
            
            # Show routing
            if hasattr(state, 'routing'):
                print(f"  Next: {state.routing.next_node}")
                if state.routing.capability_to_execute:
                    print(f"  Capability: {state.routing.capability_to_execute}")
            
            # Show completed tasks
            if hasattr(state, 'execution') and state.execution.completed_tasks:
                print(f"  Completed tasks: {list(state.execution.completed_tasks.keys())}")
            
            # Show final response
            if hasattr(state, 'core') and state.core.final_response:
                print(f"  Final response found!")
                print(f"  Type: {type(state.core.final_response)}")
                print(f"  Value: {state.core.final_response}")
    
    print(f"\n{'='*60}")
    print("Final State Check:")
    print(f"{'='*60}")
    
    if final_state and hasattr(final_state, 'core'):
        print(f"Status: {final_state.core.status}")
        print(f"Final response: {final_state.core.final_response}")
        
        if final_state.core.final_response:
            if hasattr(final_state.core.final_response, 'message'):
                print(f"Message: {final_state.core.final_response.message}")
            else:
                print(f"Response type: {type(final_state.core.final_response)}")
        
        # Check messages
        if final_state.core.messages:
            print(f"\nLast 3 messages:")
            for msg in final_state.core.messages[-3:]:
                print(f"  {msg.role}: {msg.content[:100]}...")
    else:
        print("No final state found!")


if __name__ == "__main__":
    asyncio.run(test_single_query())