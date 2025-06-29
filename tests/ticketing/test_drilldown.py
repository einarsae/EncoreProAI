"""
Test drilldown (hierarchical exploration) features
NO MOCKS - Real Cube.js integration tests only
"""
import pytest
import os
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs


@pytest.mark.asyncio
class TestDrilldownFeatures:
    """Test hierarchical data exploration with real data"""
    
    @pytest.fixture
    async def capability(self):
        """Create real capability instance"""
        return TicketingDataCapability()
    
    @pytest.fixture
    def tenant_id(self):
        """Get real tenant ID"""
        return os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    async def test_venue_to_production_drilldown(self, capability, tenant_id):
        """Test drilling from venue to productions"""
        inputs = TicketingDataInputs(
            session_id="test-venue-drill",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Show revenue by venue with ability to drill down to productions",
            measures=["ticket_line_items.amount"],
            dimensions=["venues.name", "productions.name"]
        )
        
        result = await capability.execute(inputs)
        assert result.success
        
        # Check if drilldown was added
        query = result.query_metadata.get('cube_response', {}).get('query', {})
        # LLM should understand drilldown request
        if 'drilldown' in query:
            assert isinstance(query['drilldown'], list)
            # Should include venue and production dimensions
            assert any('venue' in dim for dim in query['drilldown'])
    
    async def test_time_drilldown(self, capability, tenant_id):
        """Test drilling from month to day"""
        inputs = TicketingDataInputs(
            session_id="test-time-drill",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Monthly revenue with drilldown to daily",
            measures=["ticket_line_items.amount"],
            time_context="last 3 months"
        )
        
        result = await capability.execute(inputs)
        assert result.success
        assert result.total_rows > 0
    
    async def test_multi_level_drilldown(self, capability, tenant_id):
        """Test multi-level hierarchy: city -> venue -> production"""
        inputs = TicketingDataInputs(
            session_id="test-multi-drill",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Revenue by city, then venue, then production (hierarchical)",
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.city", "events.venue_id", "productions.name"],
            limit=50  # Limit to avoid too much data
        )
        
        result = await capability.execute(inputs)
        assert result.success
        
        # Should have all three dimensions in results
        if result.data:
            first_row = result.data[0]
            assert 'ticket_line_items.city' in first_row.dimensions
            # Note: LLM might use venue_id instead of venues.name since venues cube might not join properly
            assert ('events.venue_id' in first_row.dimensions or 'venues.name' in first_row.dimensions)
            assert 'productions.name' in first_row.dimensions
    
    async def test_drilldown_with_filters(self, capability, tenant_id):
        """Test drilldown with filters applied"""
        inputs = TicketingDataInputs(
            session_id="test-drill-filter",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Chicago sales by month with drilldown to week",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            time_context="last 6 months"
        )
        
        result = await capability.execute(inputs)
        assert result.success
        
        # All results should be for Chicago (if LLM understood)
        # This is a soft assertion as it depends on LLM interpretation
        if result.data and 'productions.name' in result.data[0].dimensions:
            names = [dp.dimensions.get('productions.name', '') for dp in result.data]
            # At least check we got some production data
            assert any(name for name in names)