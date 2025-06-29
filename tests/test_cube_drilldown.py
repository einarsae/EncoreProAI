"""
Test if drilldown is supported by our Cube.js instance
"""
import asyncio
import os
from services.cube_service import CubeService


async def test_drilldown_support():
    """Test different drilldown formats"""
    cube_url = os.getenv("CUBE_URL")
    cube_secret = os.getenv("CUBE_SECRET")
    tenant_id = os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    service = CubeService(cube_url, cube_secret)
    
    print("🧪 TESTING DRILLDOWN SUPPORT")
    print("=" * 60)
    
    # Test 1: Basic query without drilldown (should work)
    print("\n1️⃣ Basic query (no drilldown):")
    try:
        result = await service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[],
            limit=5,
            tenant_id=tenant_id
        )
        print(f"✅ Success - Got {len(result.get('data', []))} rows")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Query with drilldown=true
    print("\n2️⃣ Query with drilldown=true:")
    try:
        result = await service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name", "venues.name"],
            filters=[],
            limit=5,
            drilldown=True,
            tenant_id=tenant_id
        )
        print(f"✅ Success - Drilldown supported!")
        print(f"   Got {len(result.get('data', []))} rows")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3: Check if dimensions can be hierarchical without drilldown
    print("\n3️⃣ Multiple dimensions (no drilldown flag):")
    try:
        result = await service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["venues.name", "productions.name"],
            filters=[],
            limit=10,
            tenant_id=tenant_id
        )
        print(f"✅ Success - Got {len(result.get('data', []))} rows")
        if result.get('data'):
            first_row = result['data'][0]
            print(f"   Sample row has dimensions: {list(first_row.keys())}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 4: Check meta API for drilldown support
    print("\n4️⃣ Checking Cube.js meta for features:")
    from services.cube_meta_service import CubeMetaService
    meta_service = CubeMetaService(cube_url, cube_secret)
    try:
        meta = await meta_service.get_meta()
        # Check if any cube mentions drilldown
        for cube in meta.get('cubes', []):
            if 'drillMembers' in str(cube):
                print(f"   Found drillMembers in {cube.get('name')}")
    except Exception as e:
        print(f"   Could not check meta: {e}")
    
    print("\n" + "="*60)
    print("CONCLUSION:")
    print("If test 2 failed, drilldown is not supported by this Cube.js instance.")
    print("Use multiple dimensions (test 3) for hierarchical data instead.")


if __name__ == "__main__":
    asyncio.run(test_drilldown_support())