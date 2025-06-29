"""
Test high cardinality dimension handling
NO MOCKS - Real Cube.js integration tests only
"""
import pytest
import os
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs


@pytest.mark.asyncio
class TestHighCardinalityHandling:
    """Test handling of dimensions with many unique values"""
    
    @pytest.fixture
    async def capability(self):
        """Create real capability instance"""
        return TicketingDataCapability()
    
    @pytest.fixture
    def tenant_id(self):
        """Get real tenant ID"""
        return os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    async def test_city_dimension_with_limit(self, capability, tenant_id):
        """Test that city queries include appropriate limits"""
        inputs = TicketingDataInputs(
            session_id="test-city-limit",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Top 20 cities by revenue",
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.city"],
            limit=20
        )
        
        result = await capability.execute(inputs)
        assert result.success
        assert len(result.data) == 20
        
        # Should be ordered by revenue
        amounts = [float(dp.measures.get('ticket_line_items.amount', 0)) for dp in result.data]
        assert amounts == sorted(amounts, reverse=True)
    
    async def test_postcode_dimension_handling(self, capability, tenant_id):
        """Test postcode dimension with memory awareness"""
        inputs = TicketingDataInputs(
            session_id="test-postcode",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Revenue by postcode",
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.postcode"]
        )
        
        result = await capability.execute(inputs)
        # LLM should add a limit automatically due to high cardinality
        query = result.query_metadata.get('cube_response', {}).get('query', {})
        
        # Should have a reasonable limit
        if result.success:
            assert 'limit' in query
            assert query['limit'] <= 1000  # Should not try to get all postcodes
    
    async def test_customer_dimension_filtered(self, capability, tenant_id):
        """Test customer dimension with filters to reduce cardinality"""
        inputs = TicketingDataInputs(
            session_id="test-customer-filtered",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Top customers for Gatsby production",
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.customer_id"],
            limit=10
        )
        
        result = await capability.execute(inputs)
        assert result.success
        assert len(result.data) <= 10
    
    async def test_event_id_with_time_granularity(self, capability, tenant_id):
        """Test event ID with coarser time granularity"""
        inputs = TicketingDataInputs(
            session_id="test-event-weekly",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Weekly revenue by event for last month",
            measures=["ticket_line_items.amount"],
            dimensions=["events.id"],
            time_context="last month"
        )
        
        result = await capability.execute(inputs)
        
        # Check if LLM chose weekly granularity
        query = result.query_metadata.get('cube_response', {}).get('query', {})
        if 'timeDimensions' in query and query['timeDimensions']:
            time_dim = query['timeDimensions'][0]
            # LLM should understand to use weekly for events
            if 'granularity' in time_dim:
                assert time_dim['granularity'] in ['week', 'month']
    
    async def test_multiple_high_cardinality_dims(self, capability, tenant_id):
        """Test query with multiple high cardinality dimensions"""
        inputs = TicketingDataInputs(
            session_id="test-multi-high",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Top 50 city and postcode combinations by revenue",
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.city", "ticket_line_items.postcode"],
            limit=50
        )
        
        result = await capability.execute(inputs)
        assert result.success
        assert len(result.data) <= 50
        
        # Should have both dimensions
        if result.data:
            first_row = result.data[0]
            assert 'ticket_line_items.city' in first_row.dimensions
            assert 'ticket_line_items.postcode' in first_row.dimensions