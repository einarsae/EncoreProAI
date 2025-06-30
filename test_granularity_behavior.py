#!/usr/bin/env python3
"""
Test granularity behavior in Cube.js
"""

import asyncio
import os
from services.cube_service import CubeService

TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"

async def test_granularity():
    """Test different granularity scenarios"""
    
    cube_service = CubeService(
        cube_url=os.getenv("CUBE_URL", "https://ivory-wren.aws-us-east-2.cubecloudapp.dev/cubejs-api/v1"),
        cube_secret=os.getenv("CUBE_SECRET", "")
    )
    
    test_cases = [
        {
            "name": "Time filter WITHOUT granularity (just date range)",
            "query": {
                "measures": ["ticket_line_items.amount"],
                "dimensions": ["productions.name"],
                "filters": [],
                "time_dimensions": [{
                    "dimension": "ticket_line_items.created_at_local",
                    "dateRange": ["2024-11-01", "2024-11-30"]
                    # No granularity - just filtering
                }],
                "limit": 5,
                "tenant_id": TEST_TENANT_ID
            }
        },
        {
            "name": "Time filter WITH granularity (grouping by time)",
            "query": {
                "measures": ["ticket_line_items.amount"],
                "dimensions": ["productions.name"],
                "filters": [],
                "time_dimensions": [{
                    "dimension": "ticket_line_items.created_at_local",
                    "dateRange": ["2024-11-01", "2024-11-30"],
                    "granularity": "week"  # Group by week
                }],
                "limit": 5,
                "tenant_id": TEST_TENANT_ID
            }
        },
        {
            "name": "Time dimension with null granularity",
            "query": {
                "measures": ["ticket_line_items.amount"],
                "dimensions": ["productions.name"],
                "filters": [],
                "time_dimensions": [{
                    "dimension": "ticket_line_items.created_at_local",
                    "dateRange": ["2024-11-01", "2024-11-30"],
                    "granularity": None  # Explicit null
                }],
                "limit": 5,
                "tenant_id": TEST_TENANT_ID
            }
        },
        {
            "name": "Time dimension in dimensions array (no granularity)",
            "query": {
                "measures": ["ticket_line_items.amount"],
                "dimensions": ["productions.name", "ticket_line_items.created_at_local"],
                "filters": [],
                "limit": 5,
                "tenant_id": TEST_TENANT_ID
            }
        }
    ]
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print("-" * 60)
        
        try:
            result = await cube_service.query(**test['query'])
            print(f"✅ Success!")
            print(f"   Data rows: {len(result.get('data', []))}")
            if result.get('data'):
                # Show keys to see if time dimension is included
                print(f"   Result keys: {list(result['data'][0].keys())}")
        except Exception as e:
            print(f"❌ Failed: {str(e)[:200]}...")

async def main():
    print("Testing Cube.js Granularity Behavior")
    print("=" * 80)
    
    await test_granularity()

if __name__ == "__main__":
    asyncio.run(main())