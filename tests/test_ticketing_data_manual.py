"""
Manual test for TicketingDataCapability

This test allows you to manually verify the TicketingDataCapability
with real queries against the Cube.js API.
"""

import asyncio
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs, CubeFilter


async def test_ticketing_data_capability():
    """Test TicketingDataCapability with real queries"""
    
    print("Testing TicketingDataCapability")
    print("=" * 60)
    
    capability = TicketingDataCapability()
    
    # Test 1: Simple revenue query
    print("\n1. Simple Revenue Query (Gatsby):")
    inputs = TicketingDataInputs(
        session_id="test_session",
        tenant_id="test_tenant",
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
        for dp in result.data[:3]:  # Show first 3
            print(f"  {dp.dimensions.get('productions.name', 'Unknown')}: ${dp.measures.get('ticket_line_items.amount', 0):,.0f}")
    
    # Test 2: Top productions by revenue
    print("\n2. Top 5 Productions by Revenue:")
    inputs = TicketingDataInputs(
        session_id="test_session",
        tenant_id="test_tenant",
        user_id="test_user",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        filters=[],
        order={"ticket_line_items.amount": "desc"},
        limit=5
    )
    
    result = await capability.execute(inputs)
    if result.success and result.data:
        for i, dp in enumerate(result.data):
            name = dp.dimensions.get('productions.name', 'Unknown')
            revenue = dp.measures.get('ticket_line_items.amount', 0)
            print(f"  {i+1}. {name}: ${revenue:,.0f}")
    
    # Test 3: Multiple measures
    print("\n3. Revenue and Attendance:")
    inputs = TicketingDataInputs(
        session_id="test_session",
        tenant_id="test_tenant",
        user_id="test_user",
        measures=["ticket_line_items.amount", "ticket_line_items.quantity"],
        dimensions=["productions.name"],
        filters=[],
        order={"ticket_line_items.amount": "desc"},
        limit=3
    )
    
    result = await capability.execute(inputs)
    if result.success and result.data:
        for dp in result.data:
            name = dp.dimensions.get('productions.name', 'Unknown')
            revenue = dp.measures.get('ticket_line_items.amount', 0)
            quantity = dp.measures.get('ticket_line_items.quantity', 0)
            print(f"  {name}:")
            print(f"    Revenue: ${revenue:,.0f}")
            print(f"    Tickets: {quantity:,}")
    
    print("\nTicketingDataCapability test complete!")


if __name__ == "__main__":
    asyncio.run(test_ticketing_data_capability())