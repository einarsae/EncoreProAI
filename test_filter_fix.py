"""Test filter format fix"""

import asyncio
import json
from workflow.nodes import WorkflowNodes
from models.state import AgentState, CoreState, SemanticState
from models.frame import Frame, EntityToResolve, ResolvedEntity
from services.entity_resolver import EntityCandidate

async def test_orchestration_format():
    """Test that orchestrator generates correct filter format"""
    nodes = WorkflowNodes()
    
    # Create a state with resolved entity
    state = AgentState(
        core=CoreState(
            session_id="test",
            user_id="test",
            tenant_id="test",
            query="What is the total revenue for Chicago?"
        ),
        semantic=SemanticState(
            current_frame_id="0",  # Add this!
            frames=[Frame(
                id="f1",
                frame_id="frame1",
                query="What is the total revenue for Chicago?",
                entities=[EntityToResolve(id="e1", text="Chicago", type="production")],
                concepts=["revenue"],
                resolved_entities=[ResolvedEntity(
                    id="e1",
                    text="Chicago",
                    type="production",
                    candidates=[EntityCandidate(
                        id="prod_chicago",
                        name="Chicago",
                        entity_type="production",
                        score=0.9,
                        disambiguation="Chicago - The Musical"
                    )]
                )]
            )]
        )
    )
    
    # Build context
    context = nodes.context_builder.build_context(state)
    print("Full context:")
    print(context)
    print("\n" + "="*50 + "\n")
    
    # Get orchestration decision
    decision = await nodes._get_orchestration_decision(context)
    print(f"\nDecision action: {decision.action}")
    print(f"Capability: {decision.capability}")
    print(f"Inputs: {json.dumps(decision.inputs, indent=2)}")
    
    # Check if filters is a list
    if decision.inputs and "filters" in decision.inputs:
        filters = decision.inputs["filters"]
        print(f"\nFilter type: {type(filters)}")
        print(f"Is list: {isinstance(filters, list)}")

if __name__ == "__main__":
    asyncio.run(test_orchestration_format())