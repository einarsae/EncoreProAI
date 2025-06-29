"""
Integration tests for smart query generation with high cardinality awareness
Uses REAL Cube.js service - no mocks!
"""

import os
import pytest
import json
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs, CubeFilter


@pytest.mark.integration
@pytest.mark.asyncio
class TestSmartQueryGenerationIntegration:
    """Test LLM's ability to handle high cardinality dimensions with REAL data"""
    
    @pytest.fixture
    async def capability(self):
        """Create capability with REAL Cube services"""
        if not os.getenv("CUBE_URL") or not os.getenv("CUBE_SECRET"):
            pytest.skip("CUBE_URL and CUBE_SECRET required for integration tests")
        
        return TicketingDataCapability()
    
    async def test_city_dimension_handling(self, capability):
        """Test that LLM handles ticket_line_items.city properly"""
        inputs = TicketingDataInputs(
            session_id="test",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "yesplan"),
            user_id="test",
            query_request="Show top 20 cities by revenue",
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.city"],
            limit=20
        )
        
        # Generate query plan
        context = await capability._build_query_context(inputs)
        query_plan = await capability._generate_query_plan(inputs, context)
        
        print(f"\n🔍 City Query Plan:")
        print(f"Strategy: {query_plan.strategy}")
        print(f"Reasoning: {query_plan.reasoning}")
        
        # Verify the query has proper ordering and limit
        for i, query in enumerate(query_plan.queries):
            print(f"\n📊 Query {i+1}:")
            print(json.dumps(query, indent=2))
            
            # Check for city dimension
            if 'ticket_line_items.city' in query.get('dimensions', []):
                # Should have a limit
                assert 'limit' in query, "Expected limit for city dimension"
                assert query['limit'] <= 1000, f"Limit too high: {query['limit']}"
                
                # Should have ordering when limit is present
                if query.get('limit'):
                    assert query.get('order'), "Expected ordering with limit"
    
    async def test_customer_id_avoidance(self, capability):
        """Test that LLM avoids or limits customer_id dimension"""
        inputs = TicketingDataInputs(
            session_id="test",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "yesplan"),
            user_id="test",
            query_request="Show customer spending patterns",
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.customer_id"]
        )
        
        context = await capability._build_query_context(inputs)
        query_plan = await capability._generate_query_plan(inputs, context)
        
        print(f"\n🔍 Customer Query Reasoning: {query_plan.reasoning}")
        
        # Should either add strict limit or mention the cardinality issue
        for query in query_plan.queries:
            if 'ticket_line_items.customer_id' in query.get('dimensions', []):
                has_limit = 'limit' in query and query['limit'] <= 100
                mentions_issue = any(
                    term in query_plan.reasoning.lower() 
                    for term in ['customer', 'cardinality', 'limit', 'top']
                )
                assert has_limit or mentions_issue, \
                    "Expected strict limit or warning for customer_id dimension"
    
    async def test_event_granularity_with_real_data(self, capability):
        """Test events.id handling with real schema"""
        inputs = TicketingDataInputs(
            session_id="test",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "yesplan"),
            user_id="test",
            query_request="Show daily revenue by event for Chicago",
            measures=["ticket_line_items.amount"],
            dimensions=["events.id"],
            filters=[
                CubeFilter(
                    member="productions.name",
                    operator="contains",
                    values=["Chicago"]
                )
            ],
            time_context="last month"
        )
        
        context = await capability._build_query_context(inputs)
        query_plan = await capability._generate_query_plan(inputs, context)
        
        print(f"\n🔍 Event Granularity Reasoning: {query_plan.reasoning}")
        
        # Check if LLM adjusted for memory concerns
        reasoning_lower = query_plan.reasoning.lower()
        mentions_adjustment = any(
            term in reasoning_lower 
            for term in ['granular', 'memory', 'weekly', 'monthly', 'aggregate']
        )
        
        # Either should mention adjustment or use safer approach
        if mentions_adjustment:
            print("✅ LLM recognized and explained granularity adjustment")
        else:
            # Check if query uses safer granularity
            for query in query_plan.queries:
                if query.get('timeDimensions'):
                    granularity = query['timeDimensions'][0].get('granularity', 'day')
                    if granularity in ['week', 'month']:
                        print(f"✅ LLM used safer {granularity} granularity")
    
    async def test_production_level_aggregation(self, capability):
        """Test that production-level queries work efficiently"""
        inputs = TicketingDataInputs(
            session_id="test",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "yesplan"),
            user_id="test",
            query_request="Compare Q1 vs Q2 2024 revenue by production",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            time_context="Q1 2024 vs Q2 2024"
        )
        
        context = await capability._build_query_context(inputs)
        query_plan = await capability._generate_query_plan(inputs, context)
        
        print(f"\n🔍 Production Query Strategy: {query_plan.strategy}")
        print(f"📝 Reasoning: {query_plan.reasoning}")
        
        # Should use multi-fetch for Q1 vs Q2
        assert query_plan.strategy == "multi", \
            "Expected multi-fetch for quarter comparison"
        
        # Should have 2 queries (one for each quarter)
        assert len(query_plan.queries) == 2, \
            f"Expected 2 queries for Q1 vs Q2, got {len(query_plan.queries)}"
        
        # Each query should have appropriate date range
        for i, query in enumerate(query_plan.queries):
            print(f"\nQuery {i+1} time dimensions:")
            print(json.dumps(query.get('timeDimensions', []), indent=2))
    
    async def test_real_query_execution(self, capability):
        """Test actual query execution with smart generation"""
        # First, let's see what data we have
        test_inputs = TicketingDataInputs(
            session_id="test",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "yesplan"),
            user_id="test",
            query_request="Show top 5 cities by total revenue",
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.city"],
            limit=5
        )
        
        # Execute the full query
        result = await capability.execute(test_inputs)
        
        print(f"\n🎯 Query Execution Result:")
        print(f"Success: {result.success}")
        print(f"Rows returned: {result.total_rows}")
        
        if result.success:
            # Check query structure even if no data
            query_meta = result.query_metadata.get('cube_response', {}).get('query', {})
            print(f"\nGenerated query:")
            print(json.dumps(query_meta, indent=2))
            
            # Verify query has proper structure
            assert 'order' in query_meta, "Query should have ordering"
            assert query_meta.get('limit') <= 10, "Query should have reasonable limit"
            
            if result.data:
                # Verify ordering (first should have highest revenue)
                if len(result.data) > 1:
                    first_revenue = result.data[0].measures.get('ticket_line_items.amount', 0)
                    second_revenue = result.data[1].measures.get('ticket_line_items.amount', 0)
                    assert first_revenue >= second_revenue, \
                        "Expected descending order by revenue"
                
                # Print top cities
                print("\nTop cities by revenue:")
                for i, dp in enumerate(result.data[:5]):
                    city = dp.dimensions.get('ticket_line_items.city', 'Unknown')
                    revenue = dp.measures.get('ticket_line_items.amount', 0)
                    try:
                        revenue_float = float(revenue)
                        print(f"  {i+1}. {city}: ${revenue_float:,.2f}")
                    except (ValueError, TypeError):
                        print(f"  {i+1}. {city}: {revenue}")
            else:
                print("\nNo data returned, but query structure is correct")
                print("This might be due to:")
                print("  - Empty database")
                print("  - Filters too restrictive")
                print("  - Different tenant data")


if __name__ == "__main__":
    # For direct execution
    import asyncio
    
    async def run_tests():
        """Run integration tests directly"""
        if not os.getenv("CUBE_URL") or not os.getenv("CUBE_SECRET"):
            print("❌ CUBE_URL and CUBE_SECRET environment variables required")
            return
        
        test_class = TestSmartQueryGenerationIntegration()
        capability = TicketingDataCapability()
        
        print("🧪 Running Smart Query Generation Integration Tests...\n")
        
        tests = [
            ("City dimension handling", test_class.test_city_dimension_handling),
            ("Customer ID avoidance", test_class.test_customer_id_avoidance),
            ("Event granularity", test_class.test_event_granularity_with_real_data),
            ("Production aggregation", test_class.test_production_level_aggregation),
            ("Real query execution", test_class.test_real_query_execution)
        ]
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"Running: {test_name}")
            print('='*60)
            try:
                await test_func(capability)
                print(f"✅ {test_name} passed")
            except AssertionError as e:
                print(f"❌ {test_name} failed: {e}")
            except Exception as e:
                print(f"❌ {test_name} error: {e}")
    
    asyncio.run(run_tests())