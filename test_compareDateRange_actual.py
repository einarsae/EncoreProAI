"""
Test that compareDateRange actually works with real Cube.js
"""

import asyncio
import os
import json
from datetime import datetime
from services.cube_service import CubeService

async def test_compareDateRange_directly():
    """Test compareDateRange directly with CubeService"""
    
    cube_url = os.getenv("CUBE_URL")
    cube_secret = os.getenv("CUBE_SECRET")
    cube_service = CubeService(cube_url, cube_secret)
    
    print("Testing compareDateRange with CubeService directly...")
    
    # Test 1: Simple two-period comparison WITHOUT grouping (to avoid memory issues)
    print("\n1. Testing 2-period comparison (Jan vs Feb 2023) - total revenue:")
    try:
        result = await cube_service.query(
            measures=["ticket_line_items.amount"],
            dimensions=[],  # No grouping to reduce memory usage
            filters=[],
            time_dimensions=[{
                "dimension": "ticket_line_items.created_at_local",
                "compareDateRange": [
                    ["2023-01-01", "2023-01-31"],  # Jan 2023
                    ["2023-02-01", "2023-02-28"]   # Feb 2023
                ]
            }],
            order=[],
            limit=None,
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "default")
        )
        print(f"Success! Got {len(result.get('data', []))} rows")
        print(f"Full response: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Multi-period comparison (4 months) - total revenue
    print("\n2. Testing 4-period comparison (Jan-Apr 2023) - total revenue:")
    try:
        result = await cube_service.query(
            measures=["ticket_line_items.amount"],
            dimensions=[],  # No grouping, just totals
            filters=[],
            time_dimensions=[{
                "dimension": "ticket_line_items.created_at_local",
                "compareDateRange": [
                    ["2023-01-01", "2023-01-31"],  # Jan
                    ["2023-02-01", "2023-02-28"],  # Feb
                    ["2023-03-01", "2023-03-31"],  # Mar
                    ["2023-04-01", "2023-04-30"]   # Apr
                ]
            }],
            order=[],
            limit=None,
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "default")
        )
        print(f"Success! Got {len(result.get('data', []))} rows")
        if result.get('data'):
            print("Sample data:")
            for row in result['data'][:5]:
                print(f"  {row}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Specific production comparison across periods
    print("\n3. Testing specific production comparison (with filter):")
    try:
        result = await cube_service.query(
            measures=["ticket_line_items.amount", "ticket_line_items.quantity"],
            dimensions=[],
            filters=[{
                "member": "productions.name",
                "operator": "contains",
                "values": ["CHICAGO"]
            }],
            time_dimensions=[{
                "dimension": "ticket_line_items.created_at_local",
                "compareDateRange": [
                    ["2023-01-01", "2023-01-31"],  # Jan 2023
                    ["2023-02-01", "2023-02-28"]   # Feb 2023
                ]
            }],
            order=[],
            limit=None,
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "default")
        )
        print(f"Success! Got {len(result.get('data', []))} rows")
        if result.get('data'):
            print("Sample data:")
            for row in result['data'][:5]:
                print(f"  {row}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_compareDateRange_directly())