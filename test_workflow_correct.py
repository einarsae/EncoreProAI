"""
Test workflow with correct understanding of LangGraph
"""

import asyncio
import os
from datetime import datetime

from workflow.graph import create_workflow
from models.state import AgentState, CoreState


async def test_workflow():
    """Test workflow completion correctly"""
    
    workflow = create_workflow()
    
    initial_state = AgentState(
        core=CoreState(
            session_id="test_correct",
            tenant_id=os.getenv("DEFAULT_TENANT_ID"),
            user_id="user123",
            query="Show total revenue for November 2024",
            timestamp=datetime.utcnow()
        )
    )
    
    print(f"Query: {initial_state.core.query}")
    print("\nRunning workflow...")
    
    # Track execution
    iterations = 0
    last_state = initial_state
    
    try:
        # Stream through the workflow
        async for chunk in workflow.astream(initial_state, {"recursion_limit": 15}):
            iterations += 1
            print(f"\n{iterations}. Update keys: {list(chunk.keys())}")
            
            # Each chunk contains {node_name: state_update}
            # The state_update might be partial or full state
            
            if iterations > 10:
                print("\n⚠️ Too many iterations, stopping")
                break
        
        # After streaming, use ainvoke to get final state
        print("\n\nGetting final state with ainvoke...")
        final_result = await workflow.ainvoke(initial_state, {"recursion_limit": 15})
        
        # The result should be the final state
        print(f"\nResult type: {type(final_result)}")
        
        if isinstance(final_result, dict):
            print("Result is a dict with keys:", list(final_result.keys()))
            # Check if it has state-like structure
            if 'core' in final_result:
                core = final_result['core']
                print(f"Status: {core.status if hasattr(core, 'status') else 'unknown'}")
                print(f"Response: {core.final_response if hasattr(core, 'final_response') else 'none'}")
        elif hasattr(final_result, 'core'):
            print(f"Status: {final_result.core.status}")
            print(f"Response: {final_result.core.final_response}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_workflow())