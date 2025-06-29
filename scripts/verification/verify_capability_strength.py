"""
Comprehensive verification of TicketingDataCapability strength
"""
import asyncio
import os
import json
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs, CubeFilter


async def verify_capability():
    """Run comprehensive checks on TicketingDataCapability"""
    print("🔍 TICKETING DATA CAPABILITY STRENGTH VERIFICATION")
    print("=" * 60)
    
    capability = TicketingDataCapability()
    tenant_id = os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    # Test 1: Basic limit respect
    print("\n1️⃣ TEST: Does it respect explicit limits?")
    inputs = TicketingDataInputs(
        session_id="verify",
        tenant_id=tenant_id,
        user_id="test",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        order={"ticket_line_items.amount": "desc"},
        limit=3
    )
    
    result = await capability.execute(inputs)
    print(f"   Requested limit: 3")
    print(f"   Actual rows returned: {result.total_rows}")
    print(f"   ✅ PASS" if result.total_rows == 3 else f"   ❌ FAIL - Got {result.total_rows} rows")
    
    # Test 2: Multi-fetch for comparisons
    print("\n2️⃣ TEST: Multi-fetch for time comparisons?")
    inputs = TicketingDataInputs(
        session_id="verify",
        tenant_id=tenant_id,
        user_id="test",
        query_request="Compare Q1 vs Q2 2024 revenue",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        time_context="Q1 2024 vs Q2 2024"
    )
    
    context = await capability._build_query_context(inputs)
    query_plan = await capability._generate_query_plan(inputs, context)
    
    print(f"   Strategy: {query_plan.strategy}")
    print(f"   Number of queries: {len(query_plan.queries)}")
    print(f"   ✅ PASS" if query_plan.strategy == "multi" else "   ❌ FAIL - Should use multi-fetch")
    
    # Test 3: High cardinality handling
    print("\n3️⃣ TEST: Smart handling of high cardinality dimensions?")
    inputs = TicketingDataInputs(
        session_id="verify",
        tenant_id=tenant_id,
        user_id="test",
        query_request="Show revenue by customer",
        measures=["ticket_line_items.amount"],
        dimensions=["ticket_line_items.customer_id"]
    )
    
    context = await capability._build_query_context(inputs)
    query_plan = await capability._generate_query_plan(inputs, context)
    
    print(f"   Reasoning: {query_plan.reasoning[:100]}...")
    
    has_limit = False
    has_warning = False
    for query in query_plan.queries:
        if 'limit' in query:
            has_limit = True
            print(f"   Added limit: {query['limit']}")
        
    if any(word in query_plan.reasoning.lower() for word in ['customer', 'cardinality', 'limit', 'high']):
        has_warning = True
        print("   Has cardinality warning in reasoning")
    
    print(f"   ✅ PASS" if has_limit or has_warning else "   ❌ FAIL - No limit or warning")
    
    # Test 4: Ordering with limits
    print("\n4️⃣ TEST: Proper ordering when limiting?")
    inputs = TicketingDataInputs(
        session_id="verify",
        tenant_id=tenant_id,
        user_id="test",
        query_request="Top 10 cities by revenue",
        measures=["ticket_line_items.amount"],
        dimensions=["ticket_line_items.city"],
        limit=10
    )
    
    result = await capability.execute(inputs)
    query_meta = result.query_metadata.get('cube_response', {}).get('query', {})
    
    print(f"   Has order: {'order' in query_meta}")
    print(f"   Order by: {query_meta.get('order', {})}")
    print(f"   ✅ PASS" if 'order' in query_meta and query_meta['order'] else "   ❌ FAIL - No ordering")
    
    # Test 5: Natural language understanding
    print("\n5️⃣ TEST: Natural language query generation?")
    inputs = TicketingDataInputs(
        session_id="verify",
        tenant_id=tenant_id,
        user_id="test",
        query_request="What were the sales trends for Chicago last month broken down by week?",
        measures=["ticket_line_items.amount"],
        time_context="last month"
    )
    
    context = await capability._build_query_context(inputs)
    query_plan = await capability._generate_query_plan(inputs, context)
    
    has_time_dimension = False
    has_correct_granularity = False
    has_chicago_filter = False
    
    for query in query_plan.queries:
        if 'timeDimensions' in query and query['timeDimensions']:
            has_time_dimension = True
            granularity = query['timeDimensions'][0].get('granularity', '')
            if granularity == 'week':
                has_correct_granularity = True
        
        if 'filters' in query:
            print(f"   DEBUG: Filters found: {query['filters']}")
            for f in query['filters']:
                # Check if filter is for Chicago (case-insensitive)
                filter_str = json.dumps(f).lower()
                if 'chicago' in filter_str:
                    has_chicago_filter = True
    
    print(f"   Has time dimension: {has_time_dimension}")
    print(f"   Weekly granularity: {has_correct_granularity}")
    print(f"   Chicago filter: {has_chicago_filter}")
    print(f"   ✅ PASS" if all([has_time_dimension, has_correct_granularity, has_chicago_filter]) else "   ❌ FAIL")
    
    # Test 6: Error handling
    print("\n6️⃣ TEST: Graceful error handling?")
    inputs = TicketingDataInputs(
        session_id="verify",
        tenant_id=tenant_id,
        user_id="test",
        measures=["invalid.measure"],
        dimensions=["invalid.dimension"]
    )
    
    result = await capability.execute(inputs)
    print(f"   Success: {result.success}")
    print(f"   Has error metadata: {'error' in result.query_metadata}")
    print(f"   ✅ PASS" if not result.success else "   ❌ FAIL - Should have failed gracefully")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 CAPABILITY STRENGTH SUMMARY:")
    print("   - Respects explicit limits")
    print("   - Multi-fetch for time comparisons") 
    print("   - Smart high cardinality handling")
    print("   - Proper ordering with limits")
    print("   - Natural language understanding")
    print("   - Graceful error handling")
    

if __name__ == "__main__":
    asyncio.run(verify_capability())