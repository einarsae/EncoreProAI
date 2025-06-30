#!/usr/bin/env python3
"""
Test why LLM generates wrong order format
"""

import asyncio
import os
import json
import re
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs

TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"

async def test_llm_query_generation():
    """Test what query the LLM generates"""
    
    capability = TicketingDataCapability()
    
    # Hook into the query execution to see what's being sent
    original_execute = capability._execute_single_query
    executed_queries = []
    
    async def capture_execute(query, tenant_id):
        executed_queries.append(query)
        print("\nQuery being executed:")
        print(json.dumps(query, indent=2))
        # Don't actually execute to avoid memory issues
        return {"data": [], "total": 0}
    
    capability._execute_single_query = capture_execute
    
    # Test 1: Query that needs ordering
    print("\n" + "="*60)
    print("Test 1: Query needing order")
    print("="*60)
    
    inputs = TicketingDataInputs(
        session_id="test-order-gen",
        tenant_id=TEST_TENANT_ID,
        user_id="test-user",
        query_request="Show me ticket sales trends over time",
        measures=["ticket_line_items.amount"],
        dimensions=[]  # Let LLM decide
    )
    
    try:
        result = await capability.execute(inputs)
        print(f"\nSuccess: {result.success}")
        
        # Check the executed query
        if executed_queries:
            query = executed_queries[-1]
            if "order" in query:
                print(f"\nOrder field type: {type(query['order'])}")
                print(f"Order field value: {query['order']}")
                
                # Check if it's the wrong format
                if isinstance(query['order'], list):
                    print("❌ LLM generated list format!")
                elif isinstance(query['order'], dict):
                    print("✅ LLM generated correct dict format")
            else:
                print("No order field in query")
                
    except Exception as e:
        print(f"Error: {e}")
        # Still check what was executed
        if executed_queries:
            query = executed_queries[-1]
            print(f"\nGenerated query before error:")
            print(json.dumps(query, indent=2))

async def test_prompt_inspection():
    """Inspect the actual prompt being sent to LLM"""
    
    print("\n" + "="*60)
    print("Test 2: Inspect LLM Prompt")
    print("="*60)
    
    capability = TicketingDataCapability()
    
    # Skip context for now
    
    # Look at the prompt construction
    inputs = TicketingDataInputs(
        session_id="test-prompt",
        tenant_id=TEST_TENANT_ID,
        user_id="test-user",
        query_request="Top 5 productions by revenue",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"]
    )
    
    # Extract the prompt that would be sent
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Check for any hardcoded examples in the prompt
    prompt_file = "/app/capabilities/ticketing_data.py"
    with open(prompt_file, 'r') as f:
        content = f.read()
        
    # Find all order examples in the file
    order_examples = re.findall(r'"order":\s*([^,}]+)', content)
    print("\nOrder examples found in code:")
    for i, example in enumerate(order_examples, 1):
        print(f"{i}. {example}")
        if "[[" in example or "]]" in example:
            print("   ❌ Found array format!")

async def test_minimal_query():
    """Test with minimal direct query to isolate issue"""
    
    print("\n" + "="*60)
    print("Test 3: Minimal Direct Query")
    print("="*60)
    
    from services.cube_service import CubeService
    
    cube_service = CubeService(
        cube_url=os.getenv("CUBE_URL", "https://ivory-wren.aws-us-east-2.cubecloudapp.dev/cubejs-api/v1"),
        cube_secret=os.getenv("CUBE_SECRET", "")
    )
    
    # Test what happens with different order formats
    print("\n1. Testing with dict format:")
    try:
        result = await cube_service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[],
            order={"ticket_line_items.amount": "desc"},
            limit=5,
            tenant_id=TEST_TENANT_ID
        )
        print("✅ Dict format accepted")
    except Exception as e:
        print(f"❌ Dict format failed: {e}")
    
    print("\n2. Testing with list format:")
    try:
        result = await cube_service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[],
            order=[["ticket_line_items.amount", "desc"]],
            limit=5,
            tenant_id=TEST_TENANT_ID
        )
        print("✅ List format accepted")
    except Exception as e:
        print(f"❌ List format failed: {e}")

async def main():
    print("Testing LLM Order Format Generation")
    print("="*80)
    
    await test_llm_query_generation()
    await test_prompt_inspection()
    await test_minimal_query()

if __name__ == "__main__":
    asyncio.run(main())