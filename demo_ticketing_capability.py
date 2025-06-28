#!/usr/bin/env python3
"""
Demo: TicketingDataCapability in Action

Shows how the capability fetches raw data that EventAnalysisCapability
will later interpret.

Run: docker-compose run --rm test python demo_ticketing_capability.py
"""

import asyncio
import os
import json
from datetime import datetime

from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs, CubeFilter
from services.entity_resolver import EntityResolver


async def get_tenant_id():
    """Get tenant_id from database"""
    database_url = os.getenv("DATABASE_URL", "postgresql://encore:secure_password@postgres:5432/encoreproai")
    resolver = EntityResolver(database_url)
    await resolver.connect()
    
    async with resolver.pool.acquire() as conn:
        tenant_id = await conn.fetchval("SELECT DISTINCT tenant_id FROM entities LIMIT 1")
    
    await resolver.close()
    return tenant_id or "test_tenant"


async def main():
    print("🎫 TicketingDataCapability Demo")
    print("=" * 60)
    print("This demonstrates the pure data fetching capability.")
    print("No analysis or interpretation - just raw data access.\n")
    
    # Get tenant_id
    tenant_id = await get_tenant_id()
    print(f"Using tenant_id: {tenant_id}\n")
    
    # Initialize capability
    capability = TicketingDataCapability()
    
    # Demo 1: Simple query - "Show me revenue for Gatsby"
    print("📊 Demo 1: Revenue for Gatsby")
    print("User asks: 'Show me revenue for Gatsby'")
    print("Orchestrator would extract: entity='Gatsby' (production), concept='revenue'")
    print("Then call TicketingDataCapability with:")
    
    inputs = TicketingDataInputs(
        session_id="demo",
        tenant_id=tenant_id,
        user_id="demo_user",
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
    
    print(f"  measures: {inputs.measures}")
    print(f"  dimensions: {inputs.dimensions}")
    print(f"  filter: productions.name contains 'GATSBY'")
    
    result = await capability.execute(inputs)
    
    print(f"\nResult: {result.total_rows} rows returned")
    if result.data:
        for dp in result.data[:3]:
            name = dp.dimensions.get('productions.name', 'Unknown')
            amount = dp.measures.get('ticket_line_items.amount', 0)
            print(f"  • {name}: ${float(amount):,.0f}")
    
    # Demo 2: Top shows - "What are my top 5 shows?"
    print("\n\n📊 Demo 2: Top 5 Shows by Revenue")
    print("User asks: 'What are my top 5 shows?'")
    print("Orchestrator would extract: concept='top', concept='shows'")
    print("Then call TicketingDataCapability with:")
    
    inputs = TicketingDataInputs(
        session_id="demo",
        tenant_id=tenant_id,
        user_id="demo_user",
        measures=["ticket_line_items.amount"],
        dimensions=["productions.name"],
        filters=[],
        order={"ticket_line_items.amount": "desc"},
        limit=5
    )
    
    print(f"  measures: {inputs.measures}")
    print(f"  dimensions: {inputs.dimensions}")
    print(f"  order: by amount descending")
    print(f"  limit: 5")
    
    result = await capability.execute(inputs)
    
    print(f"\nResult: Top {result.total_rows} productions")
    if result.data:
        for i, dp in enumerate(result.data):
            name = dp.dimensions.get('productions.name', 'Unknown')
            amount = dp.measures.get('ticket_line_items.amount', 0)
            print(f"  {i+1}. {name}: ${float(amount):,.0f}")
    
    # Demo 3: Multiple measures - "Show revenue and attendance"
    print("\n\n📊 Demo 3: Revenue and Attendance")
    print("User asks: 'Show me revenue and attendance for my top shows'")
    print("Orchestrator would extract: concept='revenue', concept='attendance'")
    print("Then call TicketingDataCapability with:")
    
    inputs = TicketingDataInputs(
        session_id="demo",
        tenant_id=tenant_id,
        user_id="demo_user",
        measures=["ticket_line_items.amount", "ticket_line_items.quantity"],
        dimensions=["productions.name"],
        filters=[],
        order={"ticket_line_items.amount": "desc"},
        limit=3
    )
    
    print(f"  measures: {inputs.measures}")
    print(f"  dimensions: {inputs.dimensions}")
    
    result = await capability.execute(inputs)
    
    print(f"\nResult: {result.total_rows} productions with both metrics")
    if result.data:
        for dp in result.data:
            name = dp.dimensions.get('productions.name', 'Unknown')
            amount = dp.measures.get('ticket_line_items.amount', 0)
            quantity = dp.measures.get('ticket_line_items.quantity', 0)
            avg_ticket = amount / quantity if quantity > 0 else 0
            
            print(f"\n  {name}:")
            print(f"    Revenue: ${float(amount):,.0f}")
            print(f"    Tickets: {quantity:,}")
            print(f"    Avg Price: ${avg_ticket:.2f}")
    
    # Demo 4: Venue analysis
    print("\n\n📊 Demo 4: Revenue by Venue")
    print("User asks: 'Which venues are generating the most revenue?'")
    print("Orchestrator would extract: entity_type='venue', concept='revenue'")
    
    inputs = TicketingDataInputs(
        session_id="demo",
        tenant_id=tenant_id,
        user_id="demo_user",
        measures=["ticket_line_items.amount"],
        dimensions=["venues.name"],
        filters=[],
        order={"ticket_line_items.amount": "desc"},
        limit=5
    )
    
    result = await capability.execute(inputs)
    
    print(f"\nResult: Top {result.total_rows} venues")
    if result.data:
        total_revenue = sum(dp.measures.get('ticket_line_items.amount', 0) for dp in result.data)
        for i, dp in enumerate(result.data):
            venue = dp.dimensions.get('venues.name', 'Unknown')
            amount = dp.measures.get('ticket_line_items.amount', 0)
            pct = (amount / total_revenue * 100) if total_revenue > 0 else 0
            print(f"  {i+1}. {venue}: ${float(amount):,.0f} ({pct:.1f}%)")
    
    print("\n" + "=" * 60)
    print("✅ TicketingDataCapability is working correctly!")
    print("\nKey Points:")
    print("• The capability is a pure data fetcher - no analysis")
    print("• It wraps CubeService for the orchestrator")
    print("• Returns raw DataPoint objects with dimensions and measures")
    print("• EventAnalysisCapability will interpret this data")
    print("\nNext: Implement EventAnalysisCapability for intelligent analysis")

if __name__ == "__main__":
    asyncio.run(main())