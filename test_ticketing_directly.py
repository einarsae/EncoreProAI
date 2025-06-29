"""
Test TicketingDataCapability directly
"""

import asyncio
import os
from datetime import datetime

from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs


async def test_relative_date_query():
    """Test that relative dates are converted properly"""
    
    capability = TicketingDataCapability()
    
    # Test with relative date
    inputs = TicketingDataInputs(
        session_id="test_direct",
        tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
        user_id="user123",
        query_request="Show revenue for last month",
        measures=[]  # LLM will determine from query_request
    )
    
    print(f"Query: {inputs.query_request}")
    print(f"Today's date: {datetime.now().strftime('%Y-%m-%d')}")
    
    try:
        result = await capability.execute(inputs)
        print(f"\nSuccess: {result.success}")
        
        if result.success:
            print(f"Data points: {len(result.data)}")
            if result.data:
                print(f"First row: {result.data[0]}")
        else:
            print(f"Success: False - check logs for error")
            
        # Check what query was generated
        if hasattr(result, 'query_generated') and result.query_generated:
            print(f"\nGenerated query:")
            import json
            print(json.dumps(result.query_generated, indent=2))
            
    except Exception as e:
        print(f"\nException: {e}")
        import traceback
        traceback.print_exc()


async def test_explicit_date_query():
    """Test with explicit dates that should work"""
    
    capability = TicketingDataCapability()
    
    # Test with explicit dates
    inputs = TicketingDataInputs(
        session_id="test_explicit",
        tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
        user_id="user123",
        query_request="Show revenue for November 2024",
        measures=[]  # LLM will determine from query_request
    )
    
    print(f"\n\nQuery: {inputs.query_request}")
    
    try:
        result = await capability.execute(inputs)
        print(f"\nSuccess: {result.success}")
        
        if result.success:
            print(f"Data points: {len(result.data)}")
        else:
            print(f"Success: False - check logs for error")
            
    except Exception as e:
        print(f"\nException: {e}")


if __name__ == "__main__":
    asyncio.run(test_relative_date_query())
    asyncio.run(test_explicit_date_query())