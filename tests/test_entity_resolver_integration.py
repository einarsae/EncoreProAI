"""
Integration tests for EntityResolver with real populated data

Run: docker-compose run --rm test python -m pytest tests/test_entity_resolver_integration.py -v
"""

import pytest
import asyncio

from services.entity_resolver import EntityResolver


@pytest.mark.integration
class TestEntityResolverIntegration:
    """Test EntityResolver with real populated data"""
    
    @pytest.mark.asyncio
    async def test_production_resolution_with_disambiguation(self, database_url):
        """Test production resolution with full disambiguation"""
        resolver = EntityResolver(database_url)
        await resolver.connect()
        
        try:
            # Get actual tenant_id from database
            async with resolver.pool.acquire() as conn:
                tenant_id = await conn.fetchval("SELECT DISTINCT tenant_id FROM entities WHERE entity_type = 'production' LIMIT 1")
            
            if not tenant_id:
                pytest.skip("No production data in database")
            
            # Search for Chicago production
            candidates = await resolver.resolve_entity(
                text="chicago",
                entity_type="production",
                tenant_id=tenant_id,
                threshold=0.3
            )
            
            assert len(candidates) > 0
            
            # Check first candidate
            chicago = candidates[0]
            assert chicago.name == "CHICAGO"
            assert chicago.entity_type == "production"
            assert chicago.score >= 0.8  # Should be high score
            
            # Check disambiguation includes all required parts
            assert "[" in chicago.disambiguation  # Has ID
            assert "score:" in chicago.disambiguation  # Has score
            assert "present" in chicago.disambiguation or "-20" in chicago.disambiguation  # Has dates
            assert "$" in chicago.disambiguation or "no recent sales" in chicago.disambiguation  # Has sales info
            
        finally:
            await resolver.close()
    
    @pytest.mark.asyncio
    async def test_categorical_entity_resolution(self, database_url):
        """Test categorical entity (city) resolution"""
        resolver = EntityResolver(database_url)
        await resolver.connect()
        
        try:
            # Get actual tenant_id from database
            async with resolver.pool.acquire() as conn:
                tenant_id = await conn.fetchval("SELECT DISTINCT tenant_id FROM entities WHERE entity_type = 'city' LIMIT 1")
            
            if not tenant_id:
                pytest.skip("No city data in database")
            
            # Search for city
            candidates = await resolver.resolve_entity(
                text="new york",
                entity_type="city",
                tenant_id=tenant_id,
                threshold=0.3
            )
            
            assert len(candidates) > 0
            
            # Check city entities
            for candidate in candidates[:3]:
                assert candidate.entity_type == "city"
                assert candidate.id == candidate.name  # For categorical entities, id = name
                assert "score:" in candidate.disambiguation
                
        finally:
            await resolver.close()
    
    @pytest.mark.asyncio
    async def test_cross_type_lookup_with_discounting(self, database_url):
        """Test cross-type lookup with score discounting"""
        resolver = EntityResolver(database_url)
        await resolver.connect()
        
        try:
            # Get actual tenant_id from database
            async with resolver.pool.acquire() as conn:
                tenant_id = await conn.fetchval("SELECT DISTINCT tenant_id FROM entities LIMIT 1")
            
            if not tenant_id:
                pytest.skip("No data in database")
            
            # Search across all types
            candidates = await resolver.cross_type_lookup(
                text="chicago",
                tenant_id=tenant_id,
                threshold=0.3
            )
            
            assert len(candidates) > 0
            
            # Should find both production and city entities
            entity_types = {c.entity_type for c in candidates}
            assert "production" in entity_types or "city" in entity_types
            
            # Check score discounting
            for candidate in candidates:
                assert candidate.score <= 0.9  # All scores should be discounted
                assert f"({candidate.entity_type})" in candidate.disambiguation
                
        finally:
            await resolver.close()
    
    @pytest.mark.asyncio  
    async def test_no_results_for_nonexistent(self, database_url):
        """Test that non-existent entities return empty results"""
        resolver = EntityResolver(database_url)
        await resolver.connect()
        
        try:
            # Get actual tenant_id from database
            async with resolver.pool.acquire() as conn:
                tenant_id = await conn.fetchval("SELECT DISTINCT tenant_id FROM entities LIMIT 1")
            
            if not tenant_id:
                pytest.skip("No data in database")
            
            # Search for something that doesn't exist
            candidates = await resolver.resolve_entity(
                text="xyzabc123nonexistent",
                entity_type="production",
                tenant_id=tenant_id,
                threshold=0.3
            )
            
            assert candidates == []
            
        finally:
            await resolver.close()
    
    @pytest.mark.asyncio
    async def test_tenant_isolation(self, database_url):
        """Test that different tenants don't see each other's data"""
        resolver = EntityResolver(database_url)
        await resolver.connect()
        
        try:
            # Search with non-existent tenant
            candidates = await resolver.resolve_entity(
                text="chicago",
                entity_type="production",
                tenant_id="nonexistent_tenant_12345",
                threshold=0.3
            )
            
            assert candidates == []
            
        finally:
            await resolver.close()