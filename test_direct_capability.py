#!/usr/bin/env python3
"""
Test the ticketing_data capability directly to see if it works
"""

import asyncio
import os
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs


async def test_direct():
    """Test ticketing data capability directly"""
    
    print("Testing TicketingDataCapability directly...")
    
    capability = TicketingDataCapability()
    
    # Create inputs
    inputs = TicketingDataInputs(
        session_id="test_session",
        tenant_id=os.getenv("TENANT_ID", "yesplan"),
        user_id="test_user",
        query_request="What is the total revenue for Gatsby?",
        measures=["revenue"],
        dimensions=[],
        filters=[],
        entities=[{
            "id": "prod_gatsby_broadway",
            "name": "Gatsby",
            "type": "production"
        }]
    )
    
    try:
        print("\nExecuting capability...")
        result = await capability.execute(inputs)
        
        print(f"\nSuccess: {result.success}")
        if result.success:
            print(f"Data type: {type(result.data)}")
            if isinstance(result.data, list) and result.data:
                print(f"First record: {result.data[0]}")
            print(f"Metadata: {result.metadata}")
        else:
            print(f"Error: {result.error_message}")
            
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_direct())