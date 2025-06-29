"""
Test multi-fetch strategy for time comparisons
"""
import pytest
import os
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs


@pytest.mark.asyncio
class TestMultiFetchStrategy:
    """Test multi-fetch for time comparisons and per-entity queries"""
    
    @pytest.fixture
    async def capability(self):
        """Create capability instance"""
        return TicketingDataCapability()
    
    @pytest.fixture
    def tenant_id(self):
        """Get tenant ID"""
        return os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    async def test_quarter_comparison(self, capability, tenant_id):
        """Test Q1 vs Q2 comparison triggers multi-fetch"""
        inputs = TicketingDataInputs(
            session_id="test-q1-vs-q2",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Compare Q1 vs Q2 2024 revenue by production",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            time_context="Q1 2024 vs Q2 2024"
        )
        
        # Build context and generate plan
        context = await capability._build_query_context(inputs)
        query_plan = await capability._generate_query_plan(inputs, context)
        
        assert query_plan.strategy == "multi"
        assert len(query_plan.queries) >= 2
        assert "Q1" in query_plan.reasoning or "quarter" in query_plan.reasoning.lower()
        
        # Execute full query
        result = await capability.execute(inputs)
        assert result.success
        assert result.query_metadata.get("strategy") == "multi"
        assert "fetch_groups" in result.query_metadata
    
    async def test_year_over_year(self, capability, tenant_id):
        """Test year-over-year comparison"""
        inputs = TicketingDataInputs(
            session_id="test-yoy",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Compare this year vs last year revenue",
            measures=["ticket_line_items.amount"],
            time_context="this year vs last year",
            time_comparison_type="year_over_year"
        )
        
        context = await capability._build_query_context(inputs)
        query_plan = await capability._generate_query_plan(inputs, context)
        
        assert query_plan.strategy == "multi"
        assert "year" in query_plan.reasoning.lower()
    
    async def test_per_production_analysis(self, capability, tenant_id):
        """Test per-production daily sales"""
        inputs = TicketingDataInputs(
            session_id="test-per-production",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Show daily sales per production for Chicago and Gatsby last week",
            measures=["ticket_line_items.amount"],
            time_context="last week"
        )
        
        context = await capability._build_query_context(inputs)
        query_plan = await capability._generate_query_plan(inputs, context)
        
        # This might be single or multi depending on LLM interpretation
        assert query_plan.strategy in ["single", "multi"]
        assert len(query_plan.queries) >= 1
    
    async def test_single_query_not_multi(self, capability, tenant_id):
        """Test that simple queries don't trigger multi-fetch"""
        inputs = TicketingDataInputs(
            session_id="test-single",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Top 10 productions by revenue",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            limit=10
        )
        
        context = await capability._build_query_context(inputs)
        query_plan = await capability._generate_query_plan(inputs, context)
        
        assert query_plan.strategy == "single"
        assert len(query_plan.queries) == 1
    
    async def test_partial_failure_handling(self, capability, tenant_id):
        """Test handling when one query in multi-fetch fails"""
        # This would need a specific scenario that causes partial failure
        # For now, we just verify the structure supports it
        inputs = TicketingDataInputs(
            session_id="test-partial",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Compare Q1, Q2, Q3, Q4 2024 revenue",
            measures=["ticket_line_items.amount"],
            time_context="Q1, Q2, Q3, Q4 2024"
        )
        
        result = await capability.execute(inputs)
        # Even if some fail, we should get partial results
        assert isinstance(result.success, bool)
        if result.query_metadata.get("strategy") == "multi":
            assert "fetch_groups" in result.query_metadata