"""
Manual test for orchestration pipeline

This test runs the full orchestration with real services to verify everything is connected properly.
"""

import asyncio
import os
from datetime import datetime

from models.state import AgentState, CoreState, ExecutionState
from workflow.nodes import WorkflowNodes


async def test_simple_query():
    """Test a simple revenue query"""
    print("\n=== Testing Simple Revenue Query ===")
    
    nodes = WorkflowNodes()
    
    state = AgentState(
        core=CoreState(
            session_id="test_manual",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
            user_id="user123",
            query="Show me total revenue for all productions",
            timestamp=datetime.utcnow()
        ),
        execution=ExecutionState()
    )
    
    # Extract frames
    print("1. Extracting frames...")
    state = await nodes.extract_frames_node(state)
    print(f"   Frames: {len(state.semantic.frames)}")
    if state.semantic.frames:
        frame = state.semantic.frames[0]
        print(f"   Entities: {[e.text for e in frame.entities]}")
        print(f"   Concepts: {frame.concepts}")
    
    # Resolve entities (if any)
    if state.routing.next_node == "resolve_entities":
        print("2. Resolving entities...")
        state = await nodes.resolve_entities_node(state)
        if state.semantic.frames and state.semantic.frames[0].resolved_entities:
            for resolved in state.semantic.frames[0].resolved_entities:
                print(f"   {resolved.text} -> {resolved.candidates[0].name if resolved.candidates else 'No match'}")
    
    # Orchestrate
    print("3. Orchestrating...")
    state = await nodes.orchestrate_node(state)
    print(f"   Next node: {state.routing.next_node}")
    
    # Execute capability
    if state.routing.next_node.startswith("execute_"):
        capability = state.routing.next_node.replace("execute_", "")
        print(f"4. Executing {capability}...")
        
        if capability == "ticketing_data":
            state = await nodes.execute_ticketing_data_node(state)
        elif capability == "event_analysis":
            state = await nodes.execute_event_analysis_node(state)
        elif capability == "chat":
            state = await nodes.execute_chat_node(state)
        
        # Check result
        if state.execution.completed_tasks:
            task = list(state.execution.completed_tasks.values())[-1]
            print(f"   Success: {task.success}")
            if task.success and "data" in task.result:
                print(f"   Data points: {len(task.result['data'])}")
    
    return state


async def test_entity_query():
    """Test query with entity resolution"""
    print("\n=== Testing Entity Query (Chicago) ===")
    
    nodes = WorkflowNodes()
    
    state = AgentState(
        core=CoreState(
            session_id="test_entity",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
            user_id="user123",
            query="How much revenue did Chicago generate last month?",
            timestamp=datetime.utcnow()
        ),
        execution=ExecutionState()
    )
    
    # Run through initial steps
    state = await nodes.extract_frames_node(state)
    
    if state.routing.next_node == "resolve_entities":
        state = await nodes.resolve_entities_node(state)
    
    state = await nodes.orchestrate_node(state)
    
    # Show what orchestrator decided
    if state.core.messages:
        last_msg = state.core.messages[-1]
        if "current_task" in last_msg.metadata:
            task = last_msg.metadata["current_task"]
            print(f"Orchestrator chose: {task['capability']}")
            print(f"Inputs: {task['inputs']}")
    
    return state


async def test_analysis_query():
    """Test analysis query"""
    print("\n=== Testing Analysis Query ===")
    
    nodes = WorkflowNodes()
    
    state = AgentState(
        core=CoreState(
            session_id="test_analysis",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
            user_id="user123",
            query="Analyze the performance trends for Chicago",
            timestamp=datetime.utcnow()
        ),
        execution=ExecutionState()
    )
    
    # Run through initial steps
    state = await nodes.extract_frames_node(state)
    
    if state.routing.next_node == "resolve_entities":
        state = await nodes.resolve_entities_node(state)
    
    state = await nodes.orchestrate_node(state)
    
    # Execute first capability
    if state.routing.next_node.startswith("execute_"):
        capability = state.routing.next_node.replace("execute_", "")
        print(f"First capability: {capability}")
        
        if capability == "event_analysis":
            state = await nodes.execute_event_analysis_node(state)
            
            # Check if it needs data
            if state.execution.completed_tasks:
                task = list(state.execution.completed_tasks.values())[-1]
                if task.result.get("orchestrator_hints", {}).get("needs_data"):
                    print("Analysis requested data, orchestrating again...")
                    
                    # Orchestrate again
                    state = await nodes.orchestrate_node(state)
                    print(f"Next capability: {state.routing.next_node}")
    
    return state


async def main():
    """Run all tests"""
    print("Starting orchestration tests...")
    print(f"Using database: postgresql://encore:secure_password@postgres:5432/encoreproai")
    
    try:
        # Test 1: Simple query
        state1 = await test_simple_query()
        print(f"\nTest 1 Status: {state1.core.status}")
        
        # Test 2: Entity query
        state2 = await test_entity_query()
        print(f"\nTest 2 Status: {state2.core.status}")
        
        # Test 3: Analysis query
        state3 = await test_analysis_query()
        print(f"\nTest 3 Status: {state3.core.status}")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())