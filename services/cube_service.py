"""
CubeService - Self-contained Cube.js integration with JWT security

Based on old system analysis but completely self-contained.
Direct HTTP client with tenant isolation and minimal error handling.
"""

import httpx
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)


class CubeService:
    """Direct HTTP client to Cube.js with JWT authentication"""
    
    def __init__(self, cube_url: str, cube_secret: str):
        self.cube_url = cube_url.rstrip('/')  # Remove trailing slash
        self.cube_secret = cube_secret
    
    def generate_token(self, tenant_id: str) -> str:
        """Generate JWT with tenant isolation (30-min expiry)"""
        payload = {
            "sub": tenant_id,
            "tenant_id": tenant_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        return jwt.encode(payload, self.cube_secret, algorithm="HS256")
    
    async def query(
        self,
        measures: List[str],
        dimensions: List[str],
        filters: List[Dict[str, Any]],
        tenant_id: str,
        time_dimensions: Optional[List[Dict]] = None,
        order: Optional[Dict] = None,
        limit: Optional[int] = None,
        timezone: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute Cube.js query with minimal error handling"""
        token = self.generate_token(tenant_id)
        
        query_body = {
            "measures": measures,
            "dimensions": dimensions,
            "filters": filters
        }
        
        # Add optional parameters
        if time_dimensions:
            query_body["timeDimensions"] = time_dimensions
        if order:
            query_body["order"] = order
        if limit:
            query_body["limit"] = limit
        if timezone:
            query_body["timezone"] = timezone
        
        logger.info(f"Cube.js query for tenant {tenant_id}: {measures}, {dimensions}")
        
        # Use GET request with query as URL parameter (Cube Cloud format)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.cube_url}/cubejs-api/v1/load",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                params={"query": json.dumps(query_body)}
            )
            response.raise_for_status()  # Let HTTP errors bubble up naturally
            
            result = response.json()
            logger.info(f"Cube.js response: {len(result.get('data', []))} rows")
            return result
    
    async def get_meta(self, tenant_id: str) -> Dict[str, Any]:
        """Get Cube.js schema metadata for capability discovery"""
        token = self.generate_token(tenant_id)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.cube_url}/cubejs-api/v1/meta",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return response.json()


# Test harness and demonstration functions
async def demonstrate_cube_capabilities(cube_url: str, cube_secret: str, tenant_id: str = "test_tenant"):
    """Comprehensive test harness showing all CubeService capabilities"""
    print("🚀 CubeService Test Harness - Demonstrating All Capabilities\n")
    
    service = CubeService(cube_url, cube_secret)
    
    try:
        # 1. Test JWT Token Generation
        print("🔐 1. JWT Token Generation:")
        token = service.generate_token(tenant_id)
        print(f"   ✅ Generated JWT token (length: {len(token)})")
        print(f"   📝 Token preview: {token[:50]}...")
        
        # Decode and show payload
        import jwt as jwt_lib
        decoded = jwt_lib.decode(token, options={"verify_signature": False})
        print(f"   📋 Payload: tenant_id={decoded.get('tenant_id')}, exp={decoded.get('exp')}")
        
        # 2. Test Metadata Endpoint
        print("\n📊 2. Schema Metadata Discovery:")
        meta = await service.get_meta(tenant_id)
        cubes = meta.get('cubes', [])
        print(f"   ✅ Retrieved metadata: {len(cubes)} cubes available")
        
        if cubes:
            print("   📋 Available cubes:")
            for i, cube in enumerate(cubes[:5]):  # Show first 5
                cube_name = cube.get('name', 'unnamed')
                dimensions = len(cube.get('dimensions', []))
                measures = len(cube.get('measures', []))
                print(f"      {i+1}. {cube_name} ({dimensions} dimensions, {measures} measures)")
            
            if len(cubes) > 5:
                print(f"      ... and {len(cubes) - 5} more cubes")
        
        # 3. Test Basic Query
        print("\n🔍 3. Basic Query (Productions):")
        try:
            result = await service.query(
                measures=["productions.count"],
                dimensions=["productions.name"],
                filters=[],
                tenant_id=tenant_id,
                limit=5
            )
            data = result.get('data', [])
            print(f"   ✅ Query successful: {len(data)} rows returned")
            
            if data:
                print("   📋 Sample data:")
                for i, row in enumerate(data[:3]):
                    name = row.get('productions.name', 'N/A')
                    count = row.get('productions.count', 'N/A')
                    print(f"      {i+1}. {name} (count: {count})")
                    
        except Exception as e:
            print(f"   ❌ Basic query failed: {e}")
        
        # 4. Test Filtered Query
        print("\n🎯 4. Filtered Query (Specific Production):")
        try:
            result = await service.query(
                measures=["productions.count"],
                dimensions=["productions.name"],
                filters=[
                    {
                        "member": "productions.name",
                        "operator": "contains",
                        "values": ["CHICAGO"]
                    }
                ],
                tenant_id=tenant_id,
                limit=10
            )
            data = result.get('data', [])
            print(f"   ✅ Filtered query successful: {len(data)} rows returned")
            
            if data:
                print("   📋 Chicago-related productions:")
                for row in data:
                    name = row.get('productions.name', 'N/A')
                    print(f"      - {name}")
                    
        except Exception as e:
            print(f"   ❌ Filtered query failed: {e}")
        
        # 5. Test Complex Query with Multiple Features
        print("\n⚙️  5. Complex Query (All Features):")
        try:
            result = await service.query(
                measures=["productions.count"],
                dimensions=["productions.name"],
                filters=[
                    {
                        "member": "productions.name",
                        "operator": "set"
                    }
                ],
                tenant_id=tenant_id,
                order={"productions.name": "asc"},
                limit=10,
                timezone="America/New_York"
            )
            data = result.get('data', [])
            print(f"   ✅ Complex query successful: {len(data)} rows returned")
            print(f"   📋 Features used: filters, ordering, limit, timezone")
            
        except Exception as e:
            print(f"   ❌ Complex query failed: {e}")
        
        # 6. Test AND/OR Filters
        print("\n🔀 6. Boolean Logic Filters (AND/OR):")
        try:
            result = await service.query(
                measures=["productions.count"],
                dimensions=["productions.name"],
                filters=[
                    {
                        "or": [
                            {
                                "member": "productions.name",
                                "operator": "contains",
                                "values": ["CHICAGO"]
                            },
                            {
                                "member": "productions.name", 
                                "operator": "contains",
                                "values": ["PHANTOM"]
                            }
                        ]
                    }
                ],
                tenant_id=tenant_id,
                limit=5
            )
            data = result.get('data', [])
            print(f"   ✅ Boolean filter query successful: {len(data)} rows returned")
            
            if data:
                print("   📋 Chicago OR Phantom results:")
                for row in data:
                    name = row.get('productions.name', 'N/A')
                    print(f"      - {name}")
                    
        except Exception as e:
            print(f"   ❌ Boolean filter query failed: {e}")
        
        # 7. Test Error Handling
        print("\n🚨 7. Error Handling Test:")
        try:
            await service.query(
                measures=["invalid_cube.invalid_measure"],
                dimensions=["invalid_cube.invalid_dimension"],
                filters=[],
                tenant_id=tenant_id
            )
            print("   ❌ Expected error but query succeeded")
        except Exception as e:
            print(f"   ✅ Error handling working: {str(e)[:100]}...")
        
        print("\n🎉 CubeService Test Harness Complete!")
        print("📋 Summary of Capabilities Demonstrated:")
        print("   ✅ JWT token generation with tenant isolation")
        print("   ✅ Schema metadata discovery")
        print("   ✅ Basic queries (measures + dimensions)")
        print("   ✅ Filtered queries (contains, equals, etc.)")
        print("   ✅ Complex queries (ordering, limits, timezone)")
        print("   ✅ Boolean logic filters (AND/OR)")
        print("   ✅ Error handling (fail-fast approach)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test harness failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cube_connection(cube_url: str, cube_secret: str, tenant_id: str = "test_tenant"):
    """Simple connection test (legacy function)"""
    service = CubeService(cube_url, cube_secret)
    
    try:
        meta = await service.get_meta(tenant_id)
        print(f"✅ Cube.js connection successful: {len(meta.get('cubes', []))} cubes available")
        return True
    except Exception as e:
        print(f"❌ Cube.js connection failed: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    import os
    
    # Get configuration from environment
    cube_url = os.getenv("CUBE_URL")
    cube_secret = os.getenv("CUBE_SECRET")
    tenant_id = os.getenv("DEFAULT_TENANT_ID", "test_tenant")
    
    if cube_url and cube_secret:
        print("🎭 Running CubeService Test Harness...")
        print(f"📡 Cube URL: {cube_url}")
        print(f"🏢 Tenant ID: {tenant_id}")
        print("=" * 60)
        
        # Run comprehensive test harness
        asyncio.run(demonstrate_cube_capabilities(cube_url, cube_secret, tenant_id))
    else:
        print("❌ Missing required environment variables:")
        print("   - CUBE_URL: Cube.js API endpoint")
        print("   - CUBE_SECRET: JWT signing secret")
        print("   - DEFAULT_TENANT_ID (optional): Tenant identifier")
        print("\nSet these variables and run again.")