"""
Tests for CubeService - real connections only, no mocks

This file tests:
- JWT token generation for Cube.js authentication
- Real Cube.js API connections (requires CUBE_URL and CUBE_SECRET)
- Query construction and execution
- Error propagation (fail fast philosophy)

Run: docker-compose run --rm test python -m pytest tests/test_cube_service.py -v
Run specific test: docker-compose run --rm test python -m pytest tests/test_cube_service.py::TestCubeService::test_token_generation -v
Run only unit tests: docker-compose run --rm test python -m pytest tests/test_cube_service.py -v -m unit
"""

import pytest
import jwt
from datetime import datetime
import httpx

from services.cube_service import CubeService


class TestCubeService:
    """Test CubeService with real connections"""
    
    @pytest.mark.unit
    def test_token_generation(self, cube_config):
        """Test JWT token generation logic"""
        service = CubeService(cube_config["url"], cube_config["secret"])
        tenant_id = "test_tenant"
        
        token = service.generate_token(tenant_id)
        
        # Decode and verify token
        decoded = jwt.decode(token, cube_config["secret"], algorithms=["HS256"])
        
        assert decoded["sub"] == tenant_id
        assert decoded["tenant_id"] == tenant_id
        assert "iat" in decoded
        assert "exp" in decoded
        
        # Check expiration is ~30 minutes
        exp_time = datetime.fromtimestamp(decoded["exp"])
        iat_time = datetime.fromtimestamp(decoded["iat"])
        delta = exp_time - iat_time
        assert 29 <= delta.total_seconds() / 60 <= 31
    
    @pytest.mark.integration
    @pytest.mark.requires_cube
    async def test_cube_connection(self, cube_config):
        """Test real Cube.js connection"""
        if not cube_config["url"] or cube_config["secret"] == "test-secret":
            pytest.skip("Real CUBE_URL and CUBE_SECRET required")
        
        service = CubeService(cube_config["url"], cube_config["secret"])
        
        # Test metadata endpoint
        try:
            meta = await service.get_meta("test_tenant")
            assert "cubes" in meta
            print(f"✅ Connected to Cube.js: {len(meta.get('cubes', []))} cubes available")
        except httpx.ConnectError:
            pytest.fail("Cannot connect to Cube.js - is it running?")
        except Exception as e:
            pytest.fail(f"Cube.js connection failed: {e}")
    
    @pytest.mark.integration
    @pytest.mark.requires_cube
    async def test_cube_query(self, cube_config, real_tenant_id):
        """Test real Cube.js query"""
        if not cube_config["url"] or cube_config["secret"] == "test-secret":
            pytest.skip("Real CUBE_URL and CUBE_SECRET required")
        
        service = CubeService(cube_config["url"], cube_config["secret"])
        
        # Simple query to test connection
        result = await service.query(
            measures=["productions.count"],
            dimensions=["productions.name"],
            filters=[],  # Array format
            tenant_id=real_tenant_id,
            limit=5
        )
        
        assert "data" in result
        assert isinstance(result["data"], list)
        print(f"✅ Query returned {len(result['data'])} productions")
    
    @pytest.mark.integration
    @pytest.mark.requires_cube
    async def test_cube_query_with_measures(self, cube_config, real_tenant_id):
        """Test Cube.js query with measures and filters"""
        if not cube_config["url"] or cube_config["secret"] == "test-secret":
            pytest.skip("Real CUBE_URL and CUBE_SECRET required")
        
        service = CubeService(cube_config["url"], cube_config["secret"])
        
        # Query with ticket line items measures
        result = await service.query(
            measures=["ticket_line_items.amount", "ticket_line_items.quantity"],
            dimensions=["productions.name"],
            filters=[],  # Array format
            tenant_id=real_tenant_id,
            order={"ticket_line_items.amount": "desc"},
            limit=10
        )
        
        assert "data" in result
        data = result["data"]
        
        if data:
            # Verify data structure
            first_row = data[0]
            assert "productions.name" in first_row
            assert "ticket_line_items.amount" in first_row
            assert "ticket_line_items.quantity" in first_row
            
            # Convert amount to float for formatting (Cube.js returns strings)
            amount = float(first_row['ticket_line_items.amount'])
            print(f"✅ Top production: {first_row['productions.name']} - ${amount:,.2f}")
    
    @pytest.mark.integration
    @pytest.mark.requires_cube
    async def test_cube_time_dimension(self, cube_config, real_tenant_id):
        """Test Cube.js query with time dimensions"""
        if not cube_config["url"] or cube_config["secret"] == "test-secret":
            pytest.skip("Real CUBE_URL and CUBE_SECRET required")
        
        service = CubeService(cube_config["url"], cube_config["secret"])
        
        # Query last 30 days using actual time dimension
        result = await service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.created_at_local"],
            filters=[],  # Array format
            tenant_id=real_tenant_id,
            time_dimensions=[{
                "dimension": "ticket_line_items.created_at_local",
                "dateRange": "last 30 days"
            }],
            order={"ticket_line_items.created_at_local": "desc"},
            limit=5
        )
        
        assert "data" in result
        if result["data"]:
            print(f"✅ Found {len(result['data'])} days with sales in last 30 days")
    
    @pytest.mark.integration 
    @pytest.mark.requires_cube
    async def test_http_error_propagation(self, cube_config):
        """Test that HTTP errors propagate (fail fast)"""
        if not cube_config["url"] or cube_config["secret"] == "test-secret":
            pytest.skip("Real CUBE_URL and CUBE_SECRET required")
        
        # Use wrong secret to trigger auth error
        service = CubeService(cube_config["url"], "wrong-secret")
        
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await service.get_meta("test_tenant")
        
        # Should get 403 Forbidden or 401 Unauthorized
        assert exc_info.value.response.status_code in [401, 403]
        print(f"✅ HTTP errors propagate correctly: {exc_info.value.response.status_code}")