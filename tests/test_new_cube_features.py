"""
Test new Cube.js features (pagination, ungrouped, total)
"""
import asyncio
import os
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs


async def test_new_features():
    """Test pagination, ungrouped queries, and total count"""
    print("🧪 TESTING NEW CUBE.JS FEATURES")
    print("=" * 60)
    
    capability = TicketingDataCapability()
    tenant_id = os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    # Test 1: Pagination
    print("\n1️⃣ TEST: Pagination (Page 2)")
    inputs = TicketingDataInputs(
        session_id="test-pagination",
        tenant_id=tenant_id,
        user_id="test",
        query_request="Show page 2 of productions (10 per page)",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        limit=10
    )
    
    result = await capability.execute(inputs)
    print(f"Success: {result.success}")
    print(f"Rows returned: {result.total_rows}")
    if result.success and result.data:
        print("Productions on page 2:")
        for dp in result.data[:3]:
            print(f"  - {dp.dimensions.get('productions.name', 'Unknown')}")
    
    # Test 2: Raw data export (ungrouped)
    print("\n\n2️⃣ TEST: Raw Data Export")
    inputs = TicketingDataInputs(
        session_id="test-ungrouped",
        tenant_id=tenant_id,
        user_id="test",
        query_request="Export raw ticket transactions for Gatsby, limit to 100 rows",
        measures=[],  # No aggregation
        dimensions=[],  # No grouping
        limit=100
    )
    
    result = await capability.execute(inputs)
    print(f"Success: {result.success}")
    print(f"Raw rows returned: {result.total_rows}")
    
    # Test 3: Total count
    print("\n\n3️⃣ TEST: Get Total Count")
    inputs = TicketingDataInputs(
        session_id="test-total",
        tenant_id=tenant_id,
        user_id="test",
        query_request="Get total count of all productions with pagination info",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        limit=5
    )
    
    result = await capability.execute(inputs)
    print(f"Success: {result.success}")
    print(f"Rows returned: {result.total_rows}")
    print(f"Query metadata: {result.query_metadata}")
    
    print("\n✅ New features test complete!")


if __name__ == "__main__":
    asyncio.run(test_new_features())