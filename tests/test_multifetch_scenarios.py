"""
Test multi-fetch scenarios to ensure they work correctly
"""
import asyncio
import os
import json
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs, CubeFilter


async def test_multifetch_scenarios():
    """Test various multi-fetch scenarios"""
    print("🧪 TESTING MULTI-FETCH SCENARIOS")
    print("=" * 60)
    
    capability = TicketingDataCapability()
    tenant_id = os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    # Test 1: Q1 vs Q2 comparison
    print("\n1️⃣ TEST: Q1 vs Q2 2024 Comparison")
    inputs = TicketingDataInputs(
        session_id="test",
        tenant_id=tenant_id,
        user_id="test",
        query_request="Compare Q1 vs Q2 2024 revenue by production",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        time_context="Q1 2024 vs Q2 2024"
    )
    
    context = await capability._build_query_context(inputs)
    query_plan = await capability._generate_query_plan(inputs, context)
    
    print(f"Strategy: {query_plan.strategy}")
    print(f"Number of queries: {len(query_plan.queries)}")
    print(f"Reasoning: {query_plan.reasoning[:100]}...")
    
    if query_plan.strategy == "multi":
        for i, query in enumerate(query_plan.queries):
            print(f"\nQuery {i+1}:")
            if 'timeDimensions' in query and query['timeDimensions']:
                print(f"  Date range: {query['timeDimensions'][0].get('dateRange', 'Not specified')}")
    
    # Execute the full query
    result = await capability.execute(inputs)
    print(f"\nExecution result:")
    print(f"  Success: {result.success}")
    print(f"  Total rows: {result.total_rows}")
    if result.query_metadata.get('strategy') == 'multi':
        print(f"  Fetch groups: {result.query_metadata.get('fetch_groups', [])}")
    
    # Test 2: Per-production analysis
    print("\n\n2️⃣ TEST: Per-Production Daily Sales")
    inputs = TicketingDataInputs(
        session_id="test",
        tenant_id=tenant_id,
        user_id="test",
        query_request="Show daily sales for Chicago and Hamilton last week",
        measures=["ticket_line_items.amount"],
        time_context="last week"
    )
    
    context = await capability._build_query_context(inputs)
    query_plan = await capability._generate_query_plan(inputs, context)
    
    print(f"Strategy: {query_plan.strategy}")
    print(f"Number of queries: {len(query_plan.queries)}")
    
    # Test 3: Complex comparison
    print("\n\n3️⃣ TEST: Year-over-Year by Month")
    inputs = TicketingDataInputs(
        session_id="test",
        tenant_id=tenant_id,
        user_id="test",
        query_request="Compare this year vs last year revenue by month",
        measures=["ticket_line_items.amount"],
        time_context="this year vs last year",
        time_comparison_type="year_over_year"
    )
    
    context = await capability._build_query_context(inputs)
    query_plan = await capability._generate_query_plan(inputs, context)
    
    print(f"Strategy: {query_plan.strategy}")
    print(f"Reasoning: {query_plan.reasoning}")
    
    # Test 4: Single query (should NOT use multi-fetch)
    print("\n\n4️⃣ TEST: Simple Top 10 (Should be Single)")
    inputs = TicketingDataInputs(
        session_id="test",
        tenant_id=tenant_id,
        user_id="test",
        query_request="Top 10 productions by revenue",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        limit=10
    )
    
    context = await capability._build_query_context(inputs)
    query_plan = await capability._generate_query_plan(inputs, context)
    
    print(f"Strategy: {query_plan.strategy}")
    print(f"✅ Correct" if query_plan.strategy == "single" else "❌ Wrong - should be single")


if __name__ == "__main__":
    asyncio.run(test_multifetch_scenarios())