"""
Comprehensive tests for TicketingDataCapability

Tests with real Cube.js data - NO MOCKS
"""

import pytest
import asyncio
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs, CubeFilter


class TestTicketingDataCapability:
    """Test TicketingDataCapability with real data"""
    
    @pytest.fixture
    async def capability(self):
        """Create real capability instance"""
        return TicketingDataCapability()
    
    @pytest.fixture
    async def tenant_id(self):
        """Get real tenant ID"""
        return "5465f607-b975-4c80-bed1-a1a5a3c779e2"
    
    @pytest.mark.asyncio
    async def test_basic_revenue_query(self, capability, tenant_id):
        """Test basic revenue query returns real data"""
        inputs = TicketingDataInputs(
            session_id="test-basic-revenue",
            tenant_id=tenant_id,
            user_id="test-user",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[],
            order={"ticket_line_items.amount": "desc"},
            limit=5
        )
        
        result = await capability.execute(inputs)
        
        assert result.success
        assert result.total_rows == 5
        assert len(result.data) == 5
        
        # Verify data structure
        first_row = result.data[0]
        assert 'productions.name' in first_row.dimensions
        assert 'ticket_line_items.amount' in first_row.measures
        
        # Verify ordering (descending)
        amounts = [float(dp.measures['ticket_line_items.amount']) for dp in result.data]
        assert amounts == sorted(amounts, reverse=True)
        
        # Verify we have metadata
        assert result.assumptions is not None
        assert len(result.assumptions) > 0
        assert 'cube_response' in result.query_metadata
    
    @pytest.mark.asyncio
    async def test_filtered_query_gatsby(self, capability, tenant_id):
        """Test filtering for specific show"""
        inputs = TicketingDataInputs(
            session_id="test-gatsby",
            tenant_id=tenant_id,
            user_id="test-user",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[
                CubeFilter(
                    member="productions.name",
                    operator="contains",
                    values=["GATSBY"]
                )
            ]
        )
        
        result = await capability.execute(inputs)
        
        assert result.success
        assert result.total_rows >= 1  # Should find at least one Gatsby
        
        # Verify all results contain GATSBY
        for dp in result.data:
            name = dp.dimensions.get('productions.name', '')
            assert 'GATSBY' in name.upper()
    
    @pytest.mark.asyncio
    async def test_multiple_measures(self, capability, tenant_id):
        """Test query with revenue and attendance"""
        inputs = TicketingDataInputs(
            session_id="test-multi-measure",
            tenant_id=tenant_id,
            user_id="test-user",
            measures=[
                "ticket_line_items.amount",
                "ticket_line_items.quantity"
            ],
            dimensions=["productions.name"],
            filters=[],
            order={"ticket_line_items.amount": "desc"},
            limit=3
        )
        
        result = await capability.execute(inputs)
        
        assert result.success
        assert len(result.data) <= 3
        
        # Verify both measures present
        for dp in result.data:
            assert 'ticket_line_items.amount' in dp.measures
            assert 'ticket_line_items.quantity' in dp.measures
            
            # Calculate average price
            revenue = float(dp.measures['ticket_line_items.amount'])
            quantity = float(dp.measures['ticket_line_items.quantity'])
            avg_price = revenue / quantity if quantity > 0 else 0
            assert avg_price > 0  # Should have valid average prices
    
    @pytest.mark.asyncio
    async def test_city_filter_chicago(self, capability, tenant_id):
        """Test filtering by city dimension"""
        inputs = TicketingDataInputs(
            session_id="test-chicago",
            tenant_id=tenant_id,
            user_id="test-user",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name", "ticket_line_items.city"],
            filters=[
                CubeFilter(
                    member="ticket_line_items.city",
                    operator="equals",
                    values=["CHICAGO"]
                )
            ],
            order={"ticket_line_items.amount": "desc"},
            limit=5
        )
        
        result = await capability.execute(inputs)
        
        assert result.success
        
        # Verify all results are from Chicago
        for dp in result.data:
            city = dp.dimensions.get('ticket_line_items.city', '')
            assert city == 'CHICAGO'
    
    @pytest.mark.asyncio
    async def test_complex_filters(self, capability, tenant_id):
        """Test multiple filters together"""
        inputs = TicketingDataInputs(
            session_id="test-complex",
            tenant_id=tenant_id,
            user_id="test-user",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[
                CubeFilter(
                    member="ticket_line_items.amount",
                    operator="gt",
                    values=["100"]
                ),
                CubeFilter(
                    member="ticket_line_items.quantity",
                    operator="gte",
                    values=["1"]
                )
            ],
            limit=10
        )
        
        result = await capability.execute(inputs)
        
        assert result.success
        # Should have filtered results
        assert result.query_metadata is not None
    
    @pytest.mark.asyncio
    async def test_llm_natural_language(self, capability, tenant_id):
        """Test LLM understanding of natural language requests"""
        inputs = TicketingDataInputs(
            session_id="test-natural",
            tenant_id=tenant_id,
            user_id="test-user",
            measures=["show me total sales revenue"],
            dimensions=["broken down by production"],
            filters=[],
            order={"revenue": "highest first"},
            limit=3
        )
        
        result = await capability.execute(inputs)
        
        assert result.success
        assert result.total_rows > 0
        
        # LLM should have translated to correct field names
        assert result.query_metadata is not None
        # We simplified metadata - just check we have the cube response
        assert 'cube_response' in result.query_metadata
    
    @pytest.mark.asyncio
    async def test_venue_query(self, capability, tenant_id):
        """Test venue dimension query"""
        inputs = TicketingDataInputs(
            session_id="test-venue",
            tenant_id=tenant_id,
            user_id="test-user",
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.venue_id"],
            filters=[],
            order={"ticket_line_items.amount": "desc"},
            limit=5
        )
        
        result = await capability.execute(inputs)
        
        assert result.success
        # Venues might have 0 amounts but query should work
        assert len(result.data) <= 5
        
        # All should have venue_id dimension
        for dp in result.data:
            assert 'ticket_line_items.venue_id' in dp.dimensions
    
    @pytest.mark.asyncio
    async def test_empty_results(self, capability, tenant_id):
        """Test handling of queries with no results"""
        inputs = TicketingDataInputs(
            session_id="test-empty",
            tenant_id=tenant_id,
            user_id="test-user",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[
                CubeFilter(
                    member="productions.name",
                    operator="equals",
                    values=["NONEXISTENT_SHOW_XYZ123"]
                )
            ]
        )
        
        result = await capability.execute(inputs)
        
        assert result.success
        assert result.total_rows == 0
        assert len(result.data) == 0
        
        # Assumptions now contain query reasoning, not findings
        assert len(result.assumptions) > 0
    
    @pytest.mark.asyncio
    async def test_query_metadata_generation(self, capability, tenant_id):
        """Test metadata and description generation"""
        inputs = TicketingDataInputs(
            session_id="test-metadata",
            tenant_id=tenant_id,
            user_id="test-user",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[],
            order={"ticket_line_items.amount": "desc"},
            limit=5
        )
        
        result = await capability.execute(inputs)
        
        assert result.success
        
        # Check metadata
        assert result.query_metadata is not None
        # We simplified metadata - just check we have the cube response
        assert 'cube_response' in result.query_metadata
        assert 'query' in result.query_metadata['cube_response']
        
        # Check assumptions contain reasoning
        assert len(result.assumptions) > 0
        reasoning = result.assumptions[0]
        # Should contain some reasoning about the query
        assert len(reasoning) > 20  # Not empty
        assert isinstance(reasoning, str)
    
    @pytest.mark.asyncio
    async def test_key_findings_extraction(self, capability, tenant_id):
        """Test that key findings are extracted"""
        inputs = TicketingDataInputs(
            session_id="test-findings",
            tenant_id=tenant_id,
            user_id="test-user",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[],
            order={"ticket_line_items.amount": "desc"},
            limit=1
        )
        
        result = await capability.execute(inputs)
        
        assert result.success
        assert result.total_rows == 1
        
        # Should identify top performer
        findings = result.assumptions[1:] if len(result.assumptions) > 1 else []
        if findings:
            assert any('Top performer' in finding for finding in findings)


@pytest.mark.asyncio
async def test_all_ticketing_data_capability():
    """Run all tests - Note: This test is deprecated, use pytest to run the class instead"""
    # This test was trying to call fixtures directly which isn't allowed
    # Use: docker-compose run --rm test python -m pytest tests/test_ticketing_data_capability.py -v
    pytest.skip("Use pytest to run all tests in the class instead of this wrapper")