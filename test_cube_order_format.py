#!/usr/bin/env python3
"""
Test what order format Cube.js actually accepts
"""

import asyncio
import os
import httpx
import jwt
from datetime import datetime, timedelta

CUBE_URL = os.getenv("CUBE_URL", "https://ivory-wren.aws-us-east-2.cubecloudapp.dev/cubejs-api/v1")
CUBE_SECRET = os.getenv("CUBE_SECRET", "")
TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"

def generate_token(tenant_id: str) -> str:
    """Generate JWT token"""
    payload = {
        "sub": tenant_id,
        "tenant_id": tenant_id,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(payload, CUBE_SECRET, algorithm="HS256")

async def test_order_format(order_format, format_name):
    """Test a specific order format"""
    print(f"\nTesting {format_name}:")
    print(f"Order value: {order_format}")
    
    token = generate_token(TEST_TENANT_ID)
    
    query = {
        "measures": ["ticket_line_items.amount"],
        "dimensions": ["productions.name"],
        "limit": 2,
        "order": order_format
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{CUBE_URL}/load",
                params={"query": str(query).replace("'", '"')},
                headers=headers
            )
            
            if response.status_code == 200:
                print(f"✅ {format_name} format accepted!")
                data = response.json()
                if "data" in data and data["data"]:
                    print(f"   First result: {data['data'][0]}")
            else:
                print(f"❌ {format_name} format failed: {response.status_code}")
                print(f"   Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ {format_name} format error: {e}")

async def main():
    print("Testing Cube.js Order Format Support")
    print("="*60)
    print(f"Cube URL: {CUBE_URL}")
    print(f"Tenant: {TEST_TENANT_ID}")
    print("="*60)
    
    # Test different order formats
    await test_order_format(
        {"ticket_line_items.amount": "desc"},
        "Dict format"
    )
    
    await test_order_format(
        [["ticket_line_items.amount", "desc"]],
        "List of lists format"
    )
    
    await test_order_format(
        [{"ticket_line_items.amount": "desc"}],
        "List of dicts format"
    )
    
    # Test the specific format from the error
    await test_order_format(
        [["ticket_line_items.created_at_local", "asc"]],
        "Created at list format"
    )

if __name__ == "__main__":
    asyncio.run(main())