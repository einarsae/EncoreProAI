"""
Check available measures
"""
import asyncio
import os
from services.cube_meta_service import CubeMetaService


async def test_measures():
    """Check available measures"""
    cube_url = os.getenv("CUBE_URL")
    cube_secret = os.getenv("CUBE_SECRET")
    
    meta_service = CubeMetaService(cube_url, cube_secret)
    
    print("🔍 CHECKING AVAILABLE MEASURES")
    print("=" * 60)
    
    all_measures = await meta_service.get_all_measures()
    
    # Group by cube
    by_cube = {}
    for measure in all_measures:
        cube = measure.split('.')[0]
        if cube not in by_cube:
            by_cube[cube] = []
        by_cube[cube].append(measure)
    
    for cube, measures in sorted(by_cube.items()):
        print(f"\n{cube}:")
        for m in sorted(measures):
            print(f"  - {m}")
    
    # Check for attendance/quantity related measures
    print("\n" + "="*60)
    print("ATTENDANCE/QUANTITY MEASURES:")
    quantity_measures = [m for m in all_measures if 'quantity' in m.lower() or 'count' in m.lower() or 'attendance' in m.lower()]
    for measure in quantity_measures:
        print(f"  - {measure}")


if __name__ == "__main__":
    asyncio.run(test_measures())