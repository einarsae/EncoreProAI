#!/usr/bin/env python3
"""
Test Capability Dialogue - Test the smart translation in TicketingDataCapability
"""

import asyncio
import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs, CubeFilter

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_capability_dialogue():
    """Test the capability's ability to translate high-level requests"""
    
    print("🎯 CAPABILITY DIALOGUE TEST")
    print("=" * 60)
    print("Testing TicketingDataCapability's smart query translation")
    print("=" * 60)
    
    capability = TicketingDataCapability()
    
    # Test 1: High-level revenue request
    print("\n1️⃣ Test: High-level 'revenue' request")
    inputs = TicketingDataInputs(
        session_id="dialogue_test",
        tenant_id="5465f607-b975-4c80-bed1-a1a5a3c779e2",
        user_id="test_user",
        measures=["revenue"],  # High-level term
        dimensions=["show"],   # High-level term
        filters=[]
    )
    
    result = await capability.execute(inputs)
    print(f"✅ Success: {result.success}")
    print(f"📊 Rows returned: {result.total_rows}")
    if result.assumptions:
        print(f"💭 Assumptions: {result.assumptions}")
    
    # Test 2: Chicago performance request
    print("\n2️⃣ Test: Chicago performance (ambiguous entity)")
    inputs = TicketingDataInputs(
        session_id="dialogue_test",
        tenant_id="5465f607-b975-4c80-bed1-a1a5a3c779e2",
        user_id="test_user",
        measures=["revenue", "attendance"],
        dimensions=["time"],
        filters=[
            CubeFilter(
                member="Chicago",  # Ambiguous - could be show or city
                operator="equals",
                values=["Chicago"]
            )
        ]
    )
    
    result = await capability.execute(inputs)
    print(f"✅ Success: {result.success}")
    print(f"📊 Rows returned: {result.total_rows}")
    if not result.success:
        print(f"❌ Error: {result.query_metadata.get('translation_error', 'Unknown')}")
    
    # Test 3: Invalid request
    print("\n3️⃣ Test: Invalid measure request")
    inputs = TicketingDataInputs(
        session_id="dialogue_test",
        tenant_id="5465f607-b975-4c80-bed1-a1a5a3c779e2",
        user_id="test_user",
        measures=["happiness_index"],  # Not a real measure
        dimensions=["production"],
        filters=[]
    )
    
    result = await capability.execute(inputs)
    print(f"✅ Success: {result.success}")
    if not result.success:
        print(f"💭 Handled gracefully: {result.assumptions}")
    
    print("\n" + "=" * 60)
    print("🏁 CAPABILITY DIALOGUE TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_capability_dialogue())