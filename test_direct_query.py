#!/usr/bin/env python3
"""
Test Direct Query - Test TicketingDataCapability with proper inputs
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from capabilities.ticketing_data import TicketingDataCapability  
from models.capabilities import TicketingDataInputs, CubeFilter

async def test_direct_query():
    """Test direct query for Chicago production"""
    
    print("🎯 DIRECT QUERY TEST")
    print("=" * 60)
    
    cap = TicketingDataCapability()
    
    # Test with proper Cube.js fields
    inputs = TicketingDataInputs(
        session_id='test',
        tenant_id='5465f607-b975-4c80-bed1-a1a5a3c779e2',
        user_id='test',
        measures=['ticket_line_items.amount', 'ticket_line_items.quantity'],
        dimensions=['productions.name'],
        filters=[
            CubeFilter(
                member='productions.name',
                operator='equals', 
                values=['Chicago']
            )
        ],
        limit=5
    )
    
    result = await cap.execute(inputs)
    print(f'✅ Success: {result.success}')
    print(f'📊 Rows: {result.total_rows}')
    
    if not result.success:
        print(f'❌ Error: {result.query_metadata.get("error", "Unknown")}')
    
    if result.data:
        for dp in result.data:
            name = dp.dimensions.get("productions.name", "Unknown")
            revenue = dp.measures.get("ticket_line_items.amount", 0)
            tickets = dp.measures.get("ticket_line_items.quantity", 0)
            print(f'🎭 {name}: ${revenue:,.0f} ({tickets:,} tickets)')
    
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_direct_query())