"""
Comprehensive Capabilities Test Suite

This file tests end-to-end capability execution with real data:
- Complex time-based queries
- Multi-entity comparisons 
- Time series analysis
- Aggregations and filtering
- Real entity resolution

Run: docker-compose run --rm test python -m pytest tests/test_comprehensive_capabilities.py -v
Run specific test: docker-compose run --rm test python -m pytest tests/test_comprehensive_capabilities.py::test_top_shows_next_month -v
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import os

from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs
from services.entity_resolver import EntityResolver


@pytest.mark.integration
class TestComprehensiveCapabilities:
    """Test real-world query scenarios with actual data"""
    
    @pytest.fixture
    async def entity_resolver(self):
        """Get entity resolver for disambiguation"""
        resolver = EntityResolver()
        await resolver.connect()
        yield resolver
        await resolver.disconnect()
    
    @pytest.fixture
    def ticketing_capability(self):
        """Get ticketing data capability"""
        return TicketingDataCapability()
    
    async def test_top_ten_shows_by_sales_last_month(self, ticketing_capability, entity_resolver):
        """Test: What are my top ten show sellers next month looking at sales over the last month"""
        
        # Resolve "shows" to get production entities
        show_candidates = await entity_resolver.resolve_entity(
            text="shows",
            entity_type="productions", 
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "default")
        )
        
        # Create inputs for last month's sales
        inputs = TicketingDataInputs(
            session_id="test-top-10",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "default"),
            user_id="test-user",
            query_request="Show me top 10 productions by ticket sales from last month",
            time_context="last month",
            measures=[],  # LLM will decide
            dimensions=[],  # LLM will decide
            filters=[],  # LLM will decide
            entities=[]  # All productions
        )
        
        result = await ticketing_capability.execute(inputs)
        
        assert result.success
        assert result.total_rows > 0
        assert len(result.data) <= 10  # Should limit to top 10
        
        # Verify we got sales data
        if result.data:
            first_row = result.data[0]
            assert first_row.measures  # Should have measure data
            assert first_row.dimensions  # Should have production names
            
        print(f"\nTop 10 Shows by Sales:")
        for i, dp in enumerate(result.data[:10]):
            print(f"{i+1}. {dp.dimensions} -> {dp.measures}")
    
    async def test_compare_q1_q2_sales(self, ticketing_capability):
        """Test: Compare my sales in Q1 and Q2 this year"""
        
        current_year = datetime.now().year
        
        inputs = TicketingDataInputs(
            session_id="test-q1-q2",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "default"),
            user_id="test-user",
            query_request=f"Compare total sales between Q1 and Q2 {current_year}",
            time_context=f"Q1 {current_year} vs Q2 {current_year}",
            comparison_type="quarter_over_quarter",
            measures=[],
            dimensions=[],
            filters=[],
            entities=[]
        )
        
        result = await ticketing_capability.execute(inputs)
        
        assert result.success
        assert result.total_rows > 0
        
        # Should have comparison data
        if result.data:
            # Check for time-based comparison
            assert any("compareDateRange" in str(result.metadata) for result in [result])
            
        print(f"\nQ1 vs Q2 {current_year} Sales Comparison:")
        print(f"Query: {result.metadata.get('query_description', 'N/A')}")
        for dp in result.data[:5]:
            print(f"  {dp.dimensions} -> {dp.measures}")
    
    async def test_weekly_trends_top_5_shows(self, ticketing_capability, entity_resolver):
        """Test: Show me how my sales have been trending by week for my top 5 shows this year"""
        
        current_year = datetime.now().year
        
        inputs = TicketingDataInputs(
            session_id="test-weekly-trends",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "default"),
            user_id="test-user",
            query_request=f"Show weekly sales trends for top 5 productions in {current_year}",
            time_context=f"this year ({current_year})",
            time_granularity="week",
            measures=[],
            dimensions=[],
            filters=[],
            entities=[]
        )
        
        result = await ticketing_capability.execute(inputs)
        
        assert result.success
        assert result.total_rows > 0
        
        # Should have time series data
        if result.data:
            # Check for weekly granularity
            first_row = result.data[0]
            assert first_row.dimensions  # Should include time dimension
            
        print(f"\nWeekly Sales Trends for Top 5 Shows:")
        print(f"Total data points: {result.total_rows}")
        for i, dp in enumerate(result.data[:10]):
            print(f"  Week {i+1}: {dp.dimensions} -> {dp.measures}")
    
    async def test_specific_show_performance_ytd(self, ticketing_capability, entity_resolver):
        """Test: How has Gatsby performed year-to-date compared to last year?"""
        
        # Resolve Gatsby
        gatsby_candidates = await entity_resolver.resolve_entity(
            text="Gatsby",
            entity_type="productions",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "default")
        )
        
        inputs = TicketingDataInputs(
            session_id="test-gatsby-ytd",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "default"),
            user_id="test-user",
            query_request="Compare Gatsby performance year-to-date vs same period last year",
            time_context="year to date vs last year same period",
            comparison_type="year_over_year",
            entities=[{
                "text": "Gatsby",
                "type": "production",
                "candidates": [c.model_dump() for c in gatsby_candidates] if gatsby_candidates else []
            }],
            measures=[],
            dimensions=[],
            filters=[]
        )
        
        result = await ticketing_capability.execute(inputs)
        
        assert result.success
        
        print(f"\nGatsby YTD vs Last Year:")
        print(f"Query: {result.metadata.get('query_description', 'N/A')}")
        if result.key_findings:
            print(f"Key Findings: {result.key_findings}")
        for dp in result.data[:5]:
            print(f"  {dp.dimensions} -> {dp.measures}")
    
    async def test_venue_performance_by_month(self, ticketing_capability):
        """Test: Show venue performance by month for the last 6 months"""
        
        inputs = TicketingDataInputs(
            session_id="test-venue-monthly",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "default"),
            user_id="test-user",
            query_request="Show venue performance by month for last 6 months",
            time_context="last 6 months",
            time_granularity="month",
            measures=[],
            dimensions=[],
            filters=[],
            entities=[]
        )
        
        result = await ticketing_capability.execute(inputs)
        
        assert result.success
        assert result.total_rows > 0
        
        print(f"\nVenue Performance by Month:")
        print(f"Total venues/months: {result.total_rows}")
        for dp in result.data[:10]:
            print(f"  {dp.dimensions} -> {dp.measures}")
    
    async def test_chicago_vs_other_cities(self, ticketing_capability):
        """Test: Compare Chicago sales to other major cities"""
        
        inputs = TicketingDataInputs(
            session_id="test-city-comparison",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "default"),
            user_id="test-user",
            query_request="Compare Chicago ticket sales to New York and Los Angeles",
            entities=[],  # Cities are dimensions, not entities
            measures=[],
            dimensions=[],
            filters=[]
        )
        
        result = await ticketing_capability.execute(inputs)
        
        assert result.success
        
        print(f"\nCity Sales Comparison:")
        for dp in result.data[:10]:
            print(f"  {dp.dimensions} -> {dp.measures}")
    
    async def test_day_of_week_analysis(self, ticketing_capability):
        """Test: Which days of the week have the highest sales?"""
        
        inputs = TicketingDataInputs(
            session_id="test-dow-analysis",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "default"),
            user_id="test-user",
            query_request="Show sales by day of week for the last 3 months",
            time_context="last 3 months",
            measures=[],
            dimensions=[],
            filters=[],
            entities=[]
        )
        
        result = await ticketing_capability.execute(inputs)
        
        assert result.success
        
        print(f"\nSales by Day of Week:")
        for dp in result.data:
            print(f"  {dp.dimensions} -> {dp.measures}")
    
    async def test_price_band_analysis(self, ticketing_capability):
        """Test: Show revenue breakdown by price band for top shows"""
        
        inputs = TicketingDataInputs(
            session_id="test-price-bands",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "default"),
            user_id="test-user",
            query_request="Show revenue by price band for top 3 productions",
            measures=[],
            dimensions=[],
            filters=[],
            entities=[]
        )
        
        result = await ticketing_capability.execute(inputs)
        
        assert result.success
        
        print(f"\nRevenue by Price Band:")
        for dp in result.data[:15]:
            print(f"  {dp.dimensions} -> {dp.measures}")


# Test runner for debugging individual tests
if __name__ == "__main__":
    async def run_single_test():
        """Run a single test for debugging"""
        test = TestComprehensiveCapabilities()
        
        # Initialize fixtures
        resolver = EntityResolver()
        await resolver.connect()
        capability = TicketingDataCapability()
        
        try:
            # Run specific test
            await test.test_top_ten_shows_by_sales_last_month(capability, resolver)
        finally:
            await resolver.disconnect()
    
    # Run the test
    asyncio.run(run_single_test())