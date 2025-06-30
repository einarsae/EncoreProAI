"""
Test simple query that should complete
"""

import asyncio
import os
from datetime import datetime

from workflow.graph import create_workflow
from models.state import AgentState, CoreState


async def test_simple_complete():
    """Test simple query that should complete successfully"""
    
    workflow = create_workflow()
    
    initial_state = AgentState(
        core=CoreState(
            session_id="test_complete",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
            user_id="user123",
            query="What is the total revenue?",
            timestamp=datetime.utcnow()
        )
    )
    
    print(f"Query: {initial_state.core.query}")
    print("\nProcessing...")
    
    nodes = []
    iterations = 0
    
    try:
        async for state_update in workflow.astream(initial_state):
            iterations += 1
            
            # The update is a dict with node name as key
            for node_name in state_update:
                nodes.append(node_name)
                print(f"\n{iterations}. {node_name}")
                
                # Keep track of latest state (it's cumulative)
                if '__end__' in state_update:
                    print("   ✓ REACHED END NODE")
                    # Get the final state
                    final_state = state_update.get('__end__', {})
                    if isinstance(final_state, dict) and 'core' in final_state:
                        print(f"   Status: {final_state['core'].get('status', 'unknown')}")
                        print(f"   Response: {final_state['core'].get('final_response', {})}")
                    return
                    
                if iterations > 10:
                    print("\n⚠️  Too many iterations")
                    break
                    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print(f"\nNodes: {' → '.join(nodes)}")


if __name__ == "__main__":
    asyncio.run(test_simple_complete())