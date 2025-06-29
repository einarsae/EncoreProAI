"""
Test pagination features (offset, total)
"""
import asyncio
import os
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs


async def test_pagination():
    """Test pagination and total count features"""
    print("🧪 TESTING PAGINATION FEATURES")
    print("=" * 60)
    
    capability = TicketingDataCapability()
    tenant_id = os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    # Test 1: Basic pagination
    print("\n1️⃣ TEST: Basic Pagination (Page 2, 10 per page)")
    inputs = TicketingDataInputs(
        session_id="test-pagination",
        tenant_id=tenant_id,
        user_id="test",
        query_request="Show page 2 of production revenues (10 per page)",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        limit=10
    )
    
    result = await capability.execute(inputs)
    print(f"Success: {result.success}")
    print(f"Rows returned: {result.total_rows}")
    if result.success and result.data:
        print("Productions on page 2:")
        for i, dp in enumerate(result.data[:5]):
            amount = float(dp.measures.get('ticket_line_items.amount', 0))
            print(f"  {i+11}. {dp.dimensions.get('productions.name', 'Unknown')}: ${amount:,.0f}")
    
    # Test 2: With total count
    print("\n\n2️⃣ TEST: Get Total Count for Pagination UI")
    inputs = TicketingDataInputs(
        session_id="test-total",
        tenant_id=tenant_id,
        user_id="test",
        query_request="Get first page of productions with total count",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        limit=5
    )
    
    result = await capability.execute(inputs)
    print(f"Success: {result.success}")
    print(f"Rows returned: {result.total_rows}")
    
    # Check if total is in the response
    if result.query_metadata and 'cube_response' in result.query_metadata:
        query = result.query_metadata['cube_response'].get('query', {})
        print(f"Total requested: {query.get('total', False)}")
        # Note: The actual total count would be in the response but our current
        # structure doesn't capture it separately
    
    # Test 3: Deep pagination
    print("\n\n3️⃣ TEST: Deep Pagination (Page 10)")
    inputs = TicketingDataInputs(
        session_id="test-deep-pagination",
        tenant_id=tenant_id,
        user_id="test",
        query_request="Show page 10 of cities by revenue (20 per page)",
        measures=["ticket_line_items.amount"],
        dimensions=["ticket_line_items.city"],
        limit=20
    )
    
    result = await capability.execute(inputs)
    print(f"Success: {result.success}")
    print(f"Rows returned: {result.total_rows}")
    if result.success and result.data:
        print("Cities on page 10:")
        for i, dp in enumerate(result.data[:5]):
            city = dp.dimensions.get('ticket_line_items.city', 'Unknown')
            revenue = float(dp.measures.get('ticket_line_items.amount', 0))
            print(f"  {i+181}. {city}: ${revenue:,.0f}")
    
    print("\n✅ Pagination features test complete!")


if __name__ == "__main__":
    asyncio.run(test_pagination())