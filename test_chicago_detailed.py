"""
Test Chicago pipeline with detailed logging
"""

import asyncio
import os
import json
from datetime import datetime

from workflow.graph import create_workflow, process_query
from models.state import AgentState, CoreState, DebugState


async def test_chicago_detailed():
    """Test with detailed state inspection"""
    
    workflow = create_workflow()
    
    initial_state = AgentState(
        core=CoreState(
            session_id="test_chicago_detail",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
            user_id="user123",
            query="What is the total revenue for Chicago?"
        ),
        debug=DebugState(trace_enabled=True)
    )
    
    # Add user message
    initial_state.add_message("user", initial_state.core.query)
    
    print(f"Query: {initial_state.core.query}")
    print("\nProcessing with detailed state inspection...")
    
    states_by_node = {}
    
    async for state_update in workflow.astream(initial_state, {"recursion_limit": 15}):
        node_name = list(state_update.keys())[0] if state_update else "unknown"
        
        if node_name != '__end__':
            state = state_update.get(node_name)
            states_by_node[node_name] = state
            
            print(f"\n=== {node_name} ===")
            
            # Show key state info
            if hasattr(state, 'core'):
                print(f"Status: {state.core.status}")
                print(f"Messages: {len(state.core.messages)}")
                
            if hasattr(state, 'semantic') and state.semantic.frames:
                frame = state.semantic.frames[0]
                print(f"Frame entities: {[(e.text, e.type) for e in frame.entities]}")
                if frame.resolved_entities:
                    print(f"Resolved: {[(r.text, r.candidates[0].name if r.candidates else 'none') for r in frame.resolved_entities]}")
                    
            if hasattr(state, 'execution') and state.execution.completed_tasks:
                for task_id, result in state.execution.completed_tasks.items():
                    print(f"\nTask {task_id}:")
                    print(f"  Capability: {result.capability}")
                    print(f"  Success: {result.success}")
                    if result.capability == "ticketing_data" and result.success:
                        data = result.result.get("data", [])
                        if data:
                            print(f"  Data rows: {len(data)}")
                            if data[0].get("measures"):
                                print(f"  Measures: {data[0]['measures']}")
                                
            if hasattr(state, 'routing'):
                print(f"Next node: {state.routing.next_node}")
                
            # Check for final response
            if hasattr(state, 'core') and state.core.final_response:
                print(f"\nFINAL RESPONSE:")
                print(f"  Message: {state.core.final_response.message}")
                print(f"  Confidence: {state.core.final_response.confidence}")
    
    print("\n" + "="*50)
    print("FINAL STATE CHECK")
    print("="*50)
    
    # Get final state using ainvoke
    initial_state2 = AgentState(
        core=CoreState(
            session_id="test_chicago_final",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
            user_id="user123",
            query="What is the total revenue for Chicago?"
        )
    )
    initial_state2.add_message("user", initial_state2.core.query)
    
    final_state = await workflow.ainvoke(initial_state2, {"recursion_limit": 15})
    
    if isinstance(final_state, dict) and 'core' in final_state:
        print(f"Final status: {final_state['core'].status}")
        if final_state['core'].final_response:
            print(f"Final response: {final_state['core'].final_response.message}")
        else:
            print("No final response set!")
            
        # Check completed tasks
        if 'execution' in final_state:
            tasks = final_state['execution'].completed_tasks
            print(f"\nCompleted tasks: {list(tasks.keys())}")
            for task_id, result in tasks.items():
                if result.capability == "ticketing_data":
                    print(f"\nTicketing data result for {task_id}:")
                    data = result.result.get("data", [])
                    if data:
                        print(f"  Data: {json.dumps(data, indent=2)}")


if __name__ == "__main__":
    asyncio.run(test_chicago_detailed())