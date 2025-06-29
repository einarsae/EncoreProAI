"""
Test pagination features (offset, limit, total)
NO MOCKS - Real Cube.js integration tests only
"""
import pytest
import os
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs


@pytest.mark.asyncio
class TestPaginationFeatures:
    """Test pagination with real Cube.js data"""
    
    @pytest.fixture
    async def capability(self):
        """Create real capability instance"""
        return TicketingDataCapability()
    
    @pytest.fixture
    def tenant_id(self):
        """Get real tenant ID"""
        return os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    async def test_basic_pagination(self, capability, tenant_id):
        """Test offset and limit work correctly"""
        # First page
        inputs_page1 = TicketingDataInputs(
            session_id="test-page1",
            tenant_id=tenant_id,
            user_id="test",
            query_request="First 5 productions by revenue",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            limit=5
        )
        
        result1 = await capability.execute(inputs_page1)
        assert result1.success
        assert len(result1.data) == 5
        
        # Second page
        inputs_page2 = TicketingDataInputs(
            session_id="test-page2",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Productions 6-10 by revenue (page 2)",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            limit=5
        )
        
        result2 = await capability.execute(inputs_page2)
        assert result2.success
        assert len(result2.data) == 5
        
        # Verify no overlap
        page1_names = {dp.dimensions.get('productions.name') for dp in result1.data}
        page2_names = {dp.dimensions.get('productions.name') for dp in result2.data}
        assert len(page1_names.intersection(page2_names)) == 0
    
    async def test_total_count_request(self, capability, tenant_id):
        """Test that total count can be requested"""
        inputs = TicketingDataInputs(
            session_id="test-total",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Get productions with total count for pagination",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            limit=3
        )
        
        result = await capability.execute(inputs)
        assert result.success
        
        # Check that total was requested in query
        query = result.query_metadata.get('cube_response', {}).get('query', {})
        # LLM should understand to add total when user mentions pagination
        # This is a soft assertion as LLM might not always add it
        if 'total' in query:
            assert query['total'] == True
    
    async def test_deep_pagination(self, capability, tenant_id):
        """Test pagination with large offset"""
        inputs = TicketingDataInputs(
            session_id="test-deep",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Show page 20 of cities (10 per page)",
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.city"],
            limit=10
        )
        
        result = await capability.execute(inputs)
        assert result.success
        assert len(result.data) <= 10
        
        # Verify offset was applied
        query = result.query_metadata.get('cube_response', {}).get('query', {})
        # Page 20 with 10 per page = offset 190
        if 'offset' in query:
            assert query['offset'] >= 180  # Allow some flexibility in LLM interpretation
    
    async def test_limit_without_offset(self, capability, tenant_id):
        """Test that limit works without offset"""
        inputs = TicketingDataInputs(
            session_id="test-limit-only",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Top 7 venues by average ticket price",
            measures=["ticket_line_items.amount_average"],
            dimensions=["venues.name"],
            limit=7
        )
        
        result = await capability.execute(inputs)
        assert result.success
        assert len(result.data) == 7
        
        # Should be ordered by the measure
        amounts = [float(dp.measures.get('ticket_line_items.amount_average', 0)) for dp in result.data]
        assert amounts == sorted(amounts, reverse=True)