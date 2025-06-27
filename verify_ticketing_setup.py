#!/usr/bin/env python3
"""
Verify TicketingDataCapability setup

This script checks:
1. Environment variables are correctly set
2. CubeService can connect
3. TicketingDataCapability can fetch data

Run: docker-compose run --rm test python verify_ticketing_setup.py
"""

import asyncio
import os
import sys

async def main():
    print("🔍 Verifying TicketingDataCapability Setup")
    print("=" * 60)
    
    # Step 1: Check environment variables
    print("\n1️⃣ Checking environment variables:")
    cube_url = os.getenv("CUBE_URL")
    cube_secret = os.getenv("CUBE_SECRET")
    
    # Get tenant_id from database if available
    tenant_id = os.getenv("TENANT_ID", "test_tenant")
    try:
        from services.entity_resolver import EntityResolver
        database_url = os.getenv("DATABASE_URL", "postgresql://encore:secure_password@postgres:5432/encoreproai")
        resolver = EntityResolver(database_url)
        await resolver.connect()
        
        async with resolver.pool.acquire() as conn:
            db_tenant_id = await conn.fetchval("SELECT DISTINCT tenant_id FROM entities LIMIT 1")
            if db_tenant_id:
                tenant_id = db_tenant_id
                print(f"   ℹ️  Using tenant_id from database: {tenant_id}")
        
        await resolver.close()
    except Exception as e:
        print(f"   ℹ️  Could not get tenant_id from database: {e}")
        print(f"   ℹ️  Using default tenant_id: {tenant_id}")
    
    if cube_url:
        print(f"   ✅ CUBE_URL: {cube_url}")
    else:
        print("   ❌ CUBE_URL: NOT SET")
        print("      Note: Should be mapped from CUBE_API_URL in docker-compose.yml")
    
    if cube_secret:
        print(f"   ✅ CUBE_SECRET: {'*' * 20}{cube_secret[-4:]}")
    else:
        print("   ❌ CUBE_SECRET: NOT SET")
        print("      Note: Should be mapped from CUBE_API_SECRET in docker-compose.yml")
    
    print(f"   ℹ️  TENANT_ID: {tenant_id}")
    
    if not cube_url or not cube_secret:
        print("\n❌ Missing required environment variables. Cannot proceed.")
        sys.exit(1)
    
    # Step 2: Test CubeService
    print("\n2️⃣ Testing CubeService connection:")
    try:
        from services.cube_service import CubeService
        service = CubeService(cube_url, cube_secret)
        
        # Test token generation
        token = service.generate_token(tenant_id)
        print(f"   ✅ JWT token generated (length: {len(token)})")
        
        # Test metadata endpoint
        meta = await service.get_meta(tenant_id)
        cubes = meta.get('cubes', [])
        print(f"   ✅ Metadata retrieved: {len(cubes)} cubes available")
        
        # Test simple query
        result = await service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[],
            tenant_id=tenant_id,
            limit=1
        )
        print(f"   ✅ Test query successful: {len(result.get('data', []))} rows")
        
    except Exception as e:
        print(f"   ❌ CubeService error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Step 3: Test TicketingDataCapability
    print("\n3️⃣ Testing TicketingDataCapability:")
    try:
        from capabilities.ticketing_data import TicketingDataCapability
        from models.capabilities import TicketingDataInputs
        
        capability = TicketingDataCapability()
        print("   ✅ Capability initialized")
        
        # Test simple query
        inputs = TicketingDataInputs(
            session_id="test",
            tenant_id=tenant_id,
            user_id="test_user",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[],
            order={"ticket_line_items.amount": "desc"},
            limit=3
        )
        
        result = await capability.execute(inputs)
        print(f"   ✅ Query executed: success={result.success}, rows={result.total_rows}")
        
        if result.data:
            print("\n   Top 3 productions by revenue:")
            for i, dp in enumerate(result.data):
                name = dp.dimensions.get('productions.name', 'Unknown')
                revenue = dp.measures.get('ticket_line_items.amount', 0)
                print(f"     {i+1}. {name}: ${revenue:,.0f}")
        
    except Exception as e:
        print(f"   ❌ TicketingDataCapability error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n✅ All checks passed! TicketingDataCapability is ready to use.")
    print("\nNext steps:")
    print("1. Run test_orchestrator_with_data.py to test with the orchestrator")
    print("2. Implement EventAnalysisCapability for intelligent analysis")

if __name__ == "__main__":
    asyncio.run(main())