#!/usr/bin/env python3
"""
Test TicketingDataCapability independently

Run: docker-compose run --rm test python test_ticketing_data.py
"""

import asyncio
import os
import json

from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs, CubeFilter

async def main():
    print("🎫 Testing TicketingDataCapability")
    print("=" * 60)
    
    try:
        capability = TicketingDataCapability()
        print("✅ Capability initialized successfully")
        
        # Test 1: Get revenue for Gatsby
        print("\n1️⃣ Test: Get revenue for Gatsby")
        inputs = TicketingDataInputs(
            session_id="test",
            tenant_id=os.getenv("TENANT_ID", "test_tenant"),
            user_id="test_user",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[
                CubeFilter(
                    member="productions.name",
                    operator="contains",
                    values=["GATSBY"]
                )
            ]
        )
        
        result = await capability.execute(inputs)
        print(f"Success: {result.success}")
        print(f"Rows returned: {result.total_rows}")
        
        if result.data:
            for dp in result.data[:5]:
                name = dp.dimensions.get('productions.name', 'Unknown')
                revenue = dp.measures.get('ticket_line_items.amount', 0)
                print(f"  {name}: ${float(revenue):,.0f}")
        
        # Test 2: Top 5 productions by revenue
        print("\n2️⃣ Test: Top 5 productions by revenue")
        inputs = TicketingDataInputs(
            session_id="test",
            tenant_id=os.getenv("TENANT_ID", "test_tenant"),
            user_id="test_user",
            measures=["ticket_line_items.amount"],
            dimensions=["productions.name"],
            filters=[],
            order={"ticket_line_items.amount": "desc"},
            limit=5
        )
        
        result = await capability.execute(inputs)
        if result.success:
            print("Top productions:")
            for i, dp in enumerate(result.data):
                name = dp.dimensions.get('productions.name', 'Unknown')
                revenue = dp.measures.get('ticket_line_items.amount', 0)
                print(f"  {i+1}. {name}: ${float(revenue):,.0f}")
        
        # Test 3: Revenue by venue
        print("\n3️⃣ Test: Revenue by venue ID (top 5)")
        inputs = TicketingDataInputs(
            session_id="test",
            tenant_id=os.getenv("TENANT_ID", "test_tenant"),
            user_id="test_user",
            measures=["ticket_line_items.amount"],
            dimensions=["ticket_line_items.venue_id"],
            filters=[],
            order={"ticket_line_items.amount": "desc"},
            limit=5
        )
        
        result = await capability.execute(inputs)
        if result.success:
            print("Top venues:")
            for i, dp in enumerate(result.data):
                venue = dp.dimensions.get('ticket_line_items.venue_id', 'Unknown')
                revenue = dp.measures.get('ticket_line_items.amount', 0)
                print(f"  {i+1}. {venue}: ${float(revenue):,.0f}")
        
        # Test 4: Multiple measures
        print("\n4️⃣ Test: Revenue and attendance for top shows")
        inputs = TicketingDataInputs(
            session_id="test",
            tenant_id=os.getenv("TENANT_ID", "test_tenant"),
            user_id="test_user",
            measures=["ticket_line_items.amount", "ticket_line_items.quantity"],
            dimensions=["productions.name"],
            filters=[],
            order={"ticket_line_items.amount": "desc"},
            limit=3
        )
        
        result = await capability.execute(inputs)
        if result.success:
            for dp in result.data:
                name = dp.dimensions.get('productions.name', 'Unknown')
                revenue = dp.measures.get('ticket_line_items.amount', 0)
                quantity = dp.measures.get('ticket_line_items.quantity', 0)
                avg_price = float(revenue) / float(quantity) if float(quantity) > 0 else 0
                print(f"\n  {name}:")
                print(f"    Revenue: ${float(revenue):,.0f}")
                print(f"    Tickets: {int(quantity):,}")
                print(f"    Avg Price: ${avg_price:.2f}")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())