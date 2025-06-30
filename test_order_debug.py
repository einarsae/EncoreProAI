#!/usr/bin/env python3
"""
Debug the exact order issue from the failing test
"""

import asyncio
import os
import json
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs

TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"

async def intercept_all_queries():
    """Intercept at multiple levels to find where wrong format comes from"""
    
    capability = TicketingDataCapability()
    
    # Level 1: Intercept raw LLM response
    original_llm_invoke = None
    if hasattr(capability, 'llm'):
        original_llm_invoke = capability.llm.ainvoke
        
        async def capture_llm_response(messages):
            response = await original_llm_invoke(messages)
            print("\n=== RAW LLM RESPONSE ===")
            print(response.content[:500])
            print("======================\n")
            return response
        
        capability.llm.ainvoke = capture_llm_response
    
    # Level 2: Intercept parsed query
    original_generate = capability._generate_advanced_query
    
    async def capture_parsed_query(inputs, context):
        query = await original_generate(inputs, context)
        print("\n=== PARSED QUERY ===")
        print(json.dumps(query, indent=2))
        print("==================\n")
        return query
    
    capability._generate_advanced_query = capture_parsed_query
    
    # Level 3: Intercept cube service call
    if hasattr(capability, 'cube_service'):
        original_cube_query = capability.cube_service.query
        
        async def capture_cube_call(**kwargs):
            print("\n=== CUBE SERVICE CALL ===")
            print(f"Order parameter: {kwargs.get('order')}")
            print(f"Order type: {type(kwargs.get('order'))}")
            print("========================\n")
            # Don't actually call to avoid memory issues
            return {"data": []}
        
        capability.cube_service.query = capture_cube_call
    
    # Test the exact query that was failing
    inputs = TicketingDataInputs(
        session_id="debug-order",
        tenant_id=TEST_TENANT_ID,
        user_id="test-user",
        query_request="Analyze our ticket sales trends",  # Same as failing test
        measures=[],  # Let LLM decide
        dimensions=[]  # Let LLM decide
    )
    
    try:
        result = await capability.execute(inputs)
        print(f"\nExecution result: {result.success}")
    except Exception as e:
        print(f"\nExecution failed: {e}")

async def test_specific_order_scenario():
    """Test a query that definitely needs ordering"""
    
    print("\n" + "="*60)
    print("Testing query that requires order")
    print("="*60)
    
    capability = TicketingDataCapability()
    
    # Intercept the actual HTTP call
    if hasattr(capability, 'cube_service') and hasattr(capability.cube_service, '_client'):
        # This would show us the exact JSON being sent
        pass
    
    inputs = TicketingDataInputs(
        session_id="order-test",
        tenant_id=TEST_TENANT_ID,
        user_id="test-user",
        query_request="Show me top 10 productions by revenue sorted highest to lowest",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        order={"ticket_line_items.amount": "desc"},  # Explicitly provide correct format
        limit=10
    )
    
    # Check what happens when we provide explicit order
    print(f"\nInput order: {inputs.order}")
    print(f"Input order type: {type(inputs.order)}")
    
    # Don't execute to avoid memory issues

async def main():
    print("Debugging Order Format Issue")
    print("="*80)
    
    await intercept_all_queries()
    await test_specific_order_scenario()

if __name__ == "__main__":
    asyncio.run(main())