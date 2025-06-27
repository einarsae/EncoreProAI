"""
Tests for EntityResolver - real connections only, no mocks

Run: docker-compose run --rm test python -m pytest tests/test_entity_resolver.py -v
"""

import pytest
import asyncio
from services.entity_resolver import EntityResolver


@pytest.mark.unit
class TestEntityResolver:
    """Test entity resolver functionality"""
    
    @pytest.mark.asyncio
    async def test_database_connection(self, database_url):
        """Test database connection"""
        resolver = EntityResolver(database_url)
        await resolver.connect()
        
        # Should be able to run a simple query
        async with resolver.pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            assert result == 1
        
        await resolver.close()
        print("✅ Database connection successful")
    
    def test_score_transformation(self):
        """Test PostgreSQL score transformation algorithm"""
        resolver = EntityResolver("dummy_url")
        
        # Test exact boundaries
        assert resolver.transform_score(0.7) == 1.0
        assert resolver.transform_score(0.6) == 0.9
        assert resolver.transform_score(0.5) == 0.8
        assert abs(resolver.transform_score(0.4) - 0.575) < 0.01  # 0.5 + (0.4-0.3)*0.75 = 0.575
        assert resolver.transform_score(0.3) == 0.5
        assert resolver.transform_score(0.2) == 0.2  # Below threshold
        
        # Test intermediate values
        assert abs(resolver.transform_score(0.65) - 0.95) < 0.01
        assert abs(resolver.transform_score(0.55) - 0.85) < 0.01
        assert resolver.transform_score(0.8) == 1.0
        assert resolver.transform_score(1.0) == 1.0
        
        print("✅ Score transformation working correctly")
    
    @pytest.mark.integration
    async def test_entity_resolution_empty(self, database_url, test_tenant_id, test_db):
        """Test entity resolution with empty database"""
        resolver = EntityResolver(database_url)
        
        candidates = await resolver.resolve_entity(
            text="nonexistent",
            entity_type="production",
            tenant_id=test_tenant_id
        )
        
        assert candidates == []
        await resolver.close()
        print("✅ Empty database returns no candidates")