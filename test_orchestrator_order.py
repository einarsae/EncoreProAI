#!/usr/bin/env python3
"""
Test orchestrator's order field generation
"""

import asyncio
import os
import json
from workflow.nodes import WorkflowNodes
from models.state import AgentState, CoreState
from langchain.schema import HumanMessage, SystemMessage

TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"

async def test_orchestrator_decision():
    """Test what format the orchestrator generates for order field"""
    
    nodes = WorkflowNodes()
    
    # Create a state that should trigger ticketing_data with ordering
    state = AgentState(
        core=CoreState(
            session_id="test-order",
            user_id="test-user",
            tenant_id=TEST_TENANT_ID,
            query="Show me top 10 productions by revenue"
        )
    )
    
    # Build the context that would be sent to orchestrator
    context = nodes._build_orchestration_context(state)
    
    print("ORCHESTRATION CONTEXT:")
    print("=" * 80)
    print(context)
    print("=" * 80)
    
    # Get orchestration decision
    decision = await nodes._get_orchestration_decision(context)
    
    print("\nORCHESTRATION DECISION:")
    print("=" * 80)
    print(f"Action: {decision.action}")
    print(f"Capability: {decision.capability}")
    print(f"Inputs: {json.dumps(decision.inputs, indent=2)}")
    
    # Check the order field specifically
    if decision.inputs and "order" in decision.inputs:
        print(f"\nORDER FIELD TYPE: {type(decision.inputs['order'])}")
        print(f"ORDER FIELD VALUE: {decision.inputs['order']}")

async def main():
    print("Testing Orchestrator Order Field Generation")
    print("=" * 80)
    
    await test_orchestrator_decision()

if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        exit(1)
    
    asyncio.run(main())