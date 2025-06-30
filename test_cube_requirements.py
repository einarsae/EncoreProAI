#!/usr/bin/env python3
"""
Test Cube.js requirements - do we need measures?
"""

import asyncio
import os
from services.cube_service import CubeService

TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"

async def test_queries():
    """Test different query combinations"""
    
    cube_service = CubeService(
        cube_url=os.getenv("CUBE_URL", "https://ivory-wren.aws-us-east-2.cubecloudapp.dev/cubejs-api/v1"),
        cube_secret=os.getenv("CUBE_SECRET", "")
    )
    
    test_cases = [
        {
            "name": "No measures, no dimensions",
            "query": {
                "measures": [],
                "dimensions": [],
                "filters": [],
                "tenant_id": TEST_TENANT_ID
            }
        },
        {
            "name": "Dimensions only, no measures",
            "query": {
                "measures": [],
                "dimensions": ["productions.name"],
                "filters": [],
                "limit": 5,
                "tenant_id": TEST_TENANT_ID
            }
        },
        {
            "name": "Measures only, no dimensions",
            "query": {
                "measures": ["ticket_line_items.amount"],
                "dimensions": [],
                "filters": [],
                "tenant_id": TEST_TENANT_ID
            }
        },
        {
            "name": "Both measures and dimensions",
            "query": {
                "measures": ["ticket_line_items.amount"],
                "dimensions": ["productions.name"],
                "filters": [],
                "limit": 5,
                "tenant_id": TEST_TENANT_ID
            }
        }
    ]
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print("-" * 40)
        
        try:
            result = await cube_service.query(**test['query'])
            print(f"✅ Success!")
            print(f"   Data rows: {len(result.get('data', []))}")
            if result.get('data'):
                print(f"   First row: {result['data'][0]}")
        except Exception as e:
            print(f"❌ Failed: {str(e)[:100]}...")

async def main():
    print("Testing Cube.js Query Requirements")
    print("=" * 60)
    
    await test_queries()

if __name__ == "__main__":
    asyncio.run(main())