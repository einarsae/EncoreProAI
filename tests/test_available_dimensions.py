"""
Test what dimensions are actually available
"""
import asyncio
import os
from services.cube_meta_service import CubeMetaService


async def test_dimensions():
    """Check available dimensions"""
    cube_url = os.getenv("CUBE_URL")
    cube_secret = os.getenv("CUBE_SECRET")
    
    meta_service = CubeMetaService(cube_url, cube_secret)
    
    print("🔍 CHECKING AVAILABLE DIMENSIONS")
    print("=" * 60)
    
    all_dimensions = await meta_service.get_all_dimensions()
    
    # Group by cube
    by_cube = {}
    for dim in all_dimensions:
        cube = dim.split('.')[0]
        if cube not in by_cube:
            by_cube[cube] = []
        by_cube[cube].append(dim)
    
    for cube, dims in sorted(by_cube.items()):
        print(f"\n{cube}:")
        for dim in sorted(dims):
            print(f"  - {dim}")
    
    # Check specifically for venue dimensions
    print("\n" + "="*60)
    print("VENUE-RELATED DIMENSIONS:")
    venue_dims = [d for d in all_dimensions if 'venue' in d.lower()]
    for dim in venue_dims:
        print(f"  - {dim}")
    
    # Check for hierarchical dimensions
    print("\n" + "="*60)
    print("POTENTIAL HIERARCHIES:")
    if 'ticket_line_items.venue_id' in all_dimensions:
        print("  - ticket_line_items.venue_id -> Can join to venue details")
    if 'events.production_id' in all_dimensions:
        print("  - events.production_id -> events hierarchy")


if __name__ == "__main__":
    asyncio.run(test_dimensions())