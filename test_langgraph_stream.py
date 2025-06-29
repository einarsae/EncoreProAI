"""
Test LangGraph streaming to understand the format
"""

import asyncio
import os
from datetime import datetime

from workflow.graph import create_workflow
from models.state import AgentState, CoreState


async def test_stream_format():
    """Test to understand LangGraph stream format"""
    
    workflow = create_workflow()
    
    initial_state = AgentState(
        core=CoreState(
            session_id="test_stream",
            tenant_id=os.getenv("DEFAULT_TENANT_ID"),
            user_id="user123",
            query="Show total revenue",
            timestamp=datetime.utcnow()
        )
    )
    
    print("Starting stream...")
    
    all_updates = []
    
    async for update in workflow.astream(initial_state):
        all_updates.append(update)
        print(f"\nUpdate {len(all_updates)}:")
        print(f"  Type: {type(update)}")
        print(f"  Keys: {list(update.keys())}")
        
        # Check what's in the update
        for key, value in update.items():
            print(f"  {key}: {type(value).__name__}")
            
            # If it's the state, check status
            if hasattr(value, 'core'):
                print(f"    - Status: {value.core.status}")
                print(f"    - Next: {value.routing.next_node}")
                
                if value.core.status == "complete":
                    print("    - ✓ COMPLETE!")
                    return value
        
        if len(all_updates) > 10:
            break
    
    print(f"\nTotal updates: {len(all_updates)}")


if __name__ == "__main__":
    result = asyncio.run(test_stream_format())
    if result:
        print(f"\nFinal state status: {result.core.status}")
        print(f"Final response: {result.core.final_response}")