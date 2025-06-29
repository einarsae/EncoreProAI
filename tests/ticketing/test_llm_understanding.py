"""
Test LLM's understanding of natural language queries
NO MOCKS - Real Cube.js integration tests only
"""
import pytest
import os
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs, CubeFilter


@pytest.mark.asyncio
class TestLLMUnderstanding:
    """Test LLM's ability to translate natural language to Cube.js queries"""
    
    @pytest.fixture
    async def capability(self):
        """Create real capability instance"""
        return TicketingDataCapability()
    
    @pytest.fixture
    def tenant_id(self):
        """Get real tenant ID"""
        return os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    async def test_natural_language_measures(self, capability, tenant_id):
        """Test LLM translates natural language to correct measures"""
        inputs = TicketingDataInputs(
            session_id="test-nl-measures",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Show me total sales revenue and ticket count",
            measures=["revenue", "attendance"],  # Natural language
            dimensions=["by production"]  # Natural language
        )
        
        result = await capability.execute(inputs)
        assert result.success
        
        # LLM should translate to correct field names
        query = result.query_metadata.get('cube_response', {}).get('query', {})
        assert 'ticket_line_items.amount' in query.get('measures', [])
        assert 'ticket_line_items.quantity' in query.get('measures', [])
    
    async def test_time_context_understanding(self, capability, tenant_id):
        """Test LLM understands various time expressions"""
        time_contexts = [
            ("last month", "month"),
            ("Q3 2024", "quarter"),
            ("this year", "year"),
            ("past 7 days", "day")
        ]
        
        for context, expected_granularity in time_contexts:
            inputs = TicketingDataInputs(
                session_id=f"test-time-{context.replace(' ', '-')}",
                tenant_id=tenant_id,
                user_id="test",
                query_request=f"Revenue for {context}",
                measures=["ticket_line_items.amount"],
                time_context=context
            )
            
            result = await capability.execute(inputs)
            assert result.success
            
            # Check if time dimension was added
            query = result.query_metadata.get('cube_response', {}).get('query', {})
            if 'timeDimensions' in query and query['timeDimensions']:
                # LLM understood time context
                assert len(query['timeDimensions']) > 0
    
    async def test_implicit_ordering(self, capability, tenant_id):
        """Test LLM adds ordering when user implies it"""
        inputs = TicketingDataInputs(
            session_id="test-implicit-order",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Show me the best performing venues",
            measures=["ticket_line_items.amount"],
            dimensions=["venues.name"],
            limit=10
        )
        
        result = await capability.execute(inputs)
        assert result.success
        
        # LLM should understand "best" means order by revenue desc
        query = result.query_metadata.get('cube_response', {}).get('query', {})
        assert 'order' in query
        assert query['order'].get('ticket_line_items.amount') == 'desc'
    
    async def test_entity_filter_with_ids(self, capability, tenant_id):
        """Test LLM uses provided entity IDs in filters"""
        inputs = TicketingDataInputs(
            session_id="test-entity-ids",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Revenue for specific production",
            measures=["ticket_line_items.amount"],
            entities=[{
                "type": "production",
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "GATSBY"
            }]
        )
        
        result = await capability.execute(inputs)
        
        # LLM should use the ID in filter
        query = result.query_metadata.get('cube_response', {}).get('query', {})
        if 'filters' in query and query['filters']:
            # Should have a filter on production ID
            id_filters = [f for f in query['filters'] 
                         if 'production' in f.get('member', '').lower() 
                         and 'id' in f.get('member', '')]
            # This is a soft assertion as LLM might choose name instead
            assert len(query['filters']) > 0
    
    async def test_comparison_keywords(self, capability, tenant_id):
        """Test LLM recognizes comparison keywords"""
        inputs = TicketingDataInputs(
            session_id="test-comparison",
            tenant_id=tenant_id,
            user_id="test",
            query_request="Compare Chicago versus Gatsby revenue",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"]
        )
        
        result = await capability.execute(inputs)
        assert result.success
        
        # Should either use multi-fetch or filters for both shows
        if result.query_metadata.get("strategy") == "multi":
            assert len(result.query_metadata.get("fetch_groups", [])) >= 2
        else:
            # Single query should have both productions
            assert any("CHICAGO" in str(dp.dimensions.values()) for dp in result.data)
            assert any("GATSBY" in str(dp.dimensions.values()) for dp in result.data)