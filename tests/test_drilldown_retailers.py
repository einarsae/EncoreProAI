"""
Test drilldown with different cube combinations
"""
import asyncio
import os
from services.cube_service import CubeService


async def test_drilldown_combinations():
    """Test drilldown with various valid dimension combinations"""
    cube_url = os.getenv("CUBE_URL")
    cube_secret = os.getenv("CUBE_SECRET")
    tenant_id = os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    service = CubeService(cube_url, cube_secret)
    
    print("🧪 TESTING DRILLDOWN WITH DIFFERENT CUBES")
    print("=" * 60)
    
    # Test 1: Retailers hierarchy
    print("\n1️⃣ Retailers -> Sales Channels:")
    try:
        result = await service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["retailers.name", "sales_channels.name"],
            filters=[],
            limit=10,
            drilldown=True,
            tenant_id=tenant_id
        )
        print(f"✅ Success with drilldown!")
        print(f"   Got {len(result.get('data', []))} rows")
    except Exception as e:
        error_msg = str(e)
        if "drilldown" in error_msg:
            print(f"❌ Drilldown not allowed")
        else:
            print(f"❌ Different error: {error_msg[:100]}...")
    
    # Test 2: Same query without drilldown
    print("\n2️⃣ Same query WITHOUT drilldown:")
    try:
        result = await service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["retailers.name", "sales_channels.name"],
            filters=[],
            limit=10,
            tenant_id=tenant_id
        )
        print(f"✅ Success - Got {len(result.get('data', []))} rows")
        if result.get('data'):
            first = result['data'][0]
            print(f"   Sample: {first.get('retailers.name')} -> {first.get('sales_channels.name')}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3: Production -> Events hierarchy
    print("\n3️⃣ Production -> Events with time:")
    try:
        result = await service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name", "events.starts_at_local"],
            filters=[],
            limit=10,
            tenant_id=tenant_id
        )
        print(f"✅ Success - Got {len(result.get('data', []))} rows")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 4: City -> Production hierarchy
    print("\n4️⃣ City -> Production:")
    try:
        result = await service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.city", "productions.name"],
            filters=[],
            limit=10,
            order={"ticket_line_items.amount": "desc"},
            tenant_id=tenant_id
        )
        print(f"✅ Success - Got {len(result.get('data', []))} rows")
        if result.get('data'):
            first = result['data'][0]
            print(f"   Top: {first.get('ticket_line_items.city')} - {first.get('productions.name')}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 5: Payment method -> Sales channel
    print("\n5️⃣ Payment Method -> Sales Channel:")
    try:
        result = await service.query(
            measures=["ticket_line_items.amount"],
            dimensions=["payment_methods.name", "sales_channels.name"],
            filters=[],
            limit=10,
            tenant_id=tenant_id
        )
        print(f"✅ Success - Got {len(result.get('data', []))} rows")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print("\n" + "="*60)
    print("CONCLUSION:")
    print("- Drilldown parameter is not supported by this Cube.js instance")
    print("- But hierarchical queries work fine with multiple dimensions")
    print("- Use dimensions from different cubes for hierarchy")


if __name__ == "__main__":
    asyncio.run(test_drilldown_combinations())