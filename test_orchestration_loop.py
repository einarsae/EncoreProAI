#!/usr/bin/env python3
"""
Debug infinite orchestration loop
"""

import asyncio
import os
import json
from workflow.graph import create_workflow
from models.state import AgentState, CoreState

TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"

async def debug_orchestration_decisions():
    """Track orchestration decisions to see why it loops"""
    
    # Create initial state
    initial_state = AgentState(
        core=CoreState(
            session_id="debug-loop",
            user_id="test-user",
            tenant_id=TEST_TENANT_ID,
            query="Analyze our ticket sales trends"
        )
    )
    
    # Add user message
    initial_state.add_message("user", initial_state.core.query)
    
    # Create workflow
    workflow = create_workflow()
    
    print("Tracking Orchestration Decisions")
    print("=" * 80)
    
    step_count = 0
    orchestration_count = 0
    decisions = []
    
    try:
        async for chunk in workflow.astream(initial_state, {"recursion_limit": 10}):
            step_count += 1
            node_name = list(chunk.keys())[0] if chunk else "unknown"
            
            if node_name == "orchestrate":
                orchestration_count += 1
                print(f"\n--- Orchestration Decision #{orchestration_count} ---")
                
                state_dict = chunk["orchestrate"]
                if "core" in state_dict and "messages" in state_dict["core"]:
                    messages = state_dict["core"]["messages"]
                    
                    # Find the orchestration decision
                    for msg in reversed(messages):
                        if msg.get("role") == "system" and "current_task" in msg.get("metadata", {}):
                            task = msg["metadata"]["current_task"]
                            decisions.append(task)
                            print(f"Decision: Execute {task.get('capability')}")
                            print(f"Task ID: {task.get('id')}")
                            if task.get('inputs'):
                                print(f"Inputs summary: {list(task['inputs'].keys())}")
                            break
                    
                    # Show completed tasks
                    if "execution" in state_dict and "completed_tasks" in state_dict["execution"]:
                        completed = state_dict["execution"]["completed_tasks"]
                        print(f"Completed tasks so far: {list(completed.keys())}")
            
            elif node_name.startswith("execute_"):
                print(f"  -> Executing: {node_name}")
                
                # Check for errors
                state_dict = chunk[node_name]
                if "core" in state_dict and "messages" in state_dict["core"]:
                    messages = state_dict["core"]["messages"]
                    for msg in messages[-3:]:
                        if msg.get("role") == "system" and ("failed" in msg.get("content", "").lower() or "error" in msg.get("content", "").lower()):
                            print(f"  -> ERROR: {msg['content'][:100]}...")
            
            # Stop after reasonable number of steps
            if step_count > 20:
                print("\nStopping after 20 steps to prevent spam")
                break
                
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {str(e)}")
    
    print("\n" + "=" * 80)
    print("Summary:")
    print(f"Total steps: {step_count}")
    print(f"Orchestration decisions: {orchestration_count}")
    print(f"\nDecision sequence:")
    for i, dec in enumerate(decisions, 1):
        print(f"{i}. {dec.get('capability')} (task {dec.get('id')})")

async def check_event_analysis_behavior():
    """Check what EventAnalysis returns that might cause loops"""
    
    print("\n\nChecking EventAnalysis Behavior")
    print("=" * 80)
    
    from capabilities.event_analysis import EventAnalysisCapability
    from models.capabilities import EventAnalysisInputs, DataPoint
    
    capability = EventAnalysisCapability()
    
    # Create sample data
    sample_data = [
        DataPoint(
            dimensions={"productions.name": "Show A"},
            measures={"ticket_line_items.amount": 1000}
        ),
        DataPoint(
            dimensions={"productions.name": "Show B"},
            measures={"ticket_line_items.amount": 2000}
        )
    ]
    
    inputs = EventAnalysisInputs(
        session_id="test-ea",
        tenant_id=TEST_TENANT_ID,
        user_id="test-user",
        analysis_request="Analyze ticket sales trends",
        data=sample_data
    )
    
    result = await capability.execute(inputs)
    
    print(f"Success: {result.success}")
    print(f"Analysis complete: {result.analysis_complete}")
    print(f"Orchestrator hints: {json.dumps(result.orchestrator_hints, indent=2)}")
    
    # Check if it's asking for more data
    if result.orchestrator_hints and result.orchestrator_hints.get("needs_more_data"):
        print("\n⚠️  EventAnalysis is requesting more data!")
        print(f"Next capability: {result.orchestrator_hints.get('next_capability')}")

async def main():
    await debug_orchestration_decisions()
    await check_event_analysis_behavior()

if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        exit(1)
    
    asyncio.run(main())