#!/usr/bin/env python3
"""
Test ticketing_data capability directly to isolate order field issue
"""

import asyncio
import os
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs

TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"

async def test_with_dict_order():
    """Test with dict format order"""
    print("\n1. Testing with dict format order")
    print("=" * 60)
    
    capability = TicketingDataCapability()
    
    inputs = TicketingDataInputs(
        session_id="test-dict-order",
        tenant_id=TEST_TENANT_ID,
        user_id="test-user",
        query_request="Get top 5 productions by revenue",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        order={"ticket_line_items.amount": "desc"},
        limit=5
    )
    
    print(f"Input order: {inputs.order}")
    print(f"Input order type: {type(inputs.order)}")
    
    try:
        result = await capability.execute(inputs)
        print(f"\n✅ Success!")
        print(f"Rows returned: {result.total_rows}")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")

async def test_without_order():
    """Test without order field"""
    print("\n\n2. Testing without order field")
    print("=" * 60)
    
    capability = TicketingDataCapability()
    
    inputs = TicketingDataInputs(
        session_id="test-no-order",
        tenant_id=TEST_TENANT_ID,
        user_id="test-user",
        query_request="Get all production revenues",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        limit=5
    )
    
    print(f"Input order: {inputs.order}")
    
    try:
        result = await capability.execute(inputs)
        print(f"\n✅ Success!")
        print(f"Rows returned: {result.total_rows}")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")

async def test_with_natural_language():
    """Test with natural language request that implies ordering"""
    print("\n\n3. Testing with natural language implying order")
    print("=" * 60)
    
    capability = TicketingDataCapability()
    
    inputs = TicketingDataInputs(
        session_id="test-nl-order",
        tenant_id=TEST_TENANT_ID,
        user_id="test-user",
        query_request="Show me our ticket sales trends over time",
        measures=["ticket_line_items.amount"],
        dimensions=[]  # Let the LLM decide
    )
    
    print(f"Query request: {inputs.query_request}")
    print(f"Input order: {inputs.order}")
    
    try:
        result = await capability.execute(inputs)
        print(f"\n✅ Success!")
        print(f"Rows returned: {result.total_rows}")
        print(f"Query description: {result.query_description}")
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)[:200]}...")

async def main():
    print("Testing TicketingDataCapability Order Field Handling")
    print("=" * 80)
    print(f"Tenant: {TEST_TENANT_ID}")
    print("=" * 80)
    
    await test_with_dict_order()
    await test_without_order()
    await test_with_natural_language()

if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        exit(1)
    
    asyncio.run(main())