#!/usr/bin/env python3
"""
Test what queries are generated for "analyze ticket sales trends"
"""

import asyncio
import os
import json
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs

TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"

async def test_query_generation():
    """See what query is generated for the problematic request"""
    
    capability = TicketingDataCapability()
    
    # Hook into the query generation
    queries_generated = []
    original_execute_single = capability._execute_single_query
    
    async def capture_query(query, tenant_id):
        queries_generated.append(query)
        print("\n=== GENERATED QUERY ===")
        print(json.dumps(query, indent=2))
        
        # Calculate approximate data size
        measures = len(query.get("measures", []))
        dimensions = len(query.get("dimensions", []))
        filters = len(query.get("filters", []))
        has_time = bool(query.get("timeDimensions"))
        
        print(f"\nQuery complexity:")
        print(f"  Measures: {measures}")
        print(f"  Dimensions: {dimensions}")
        print(f"  Filters: {filters}")
        print(f"  Time dimensions: {has_time}")
        print(f"  Limit: {query.get('limit', 'NONE')}")
        
        # Don't actually execute
        return {"data": [], "total": 0}
    
    capability._execute_single_query = capture_query
    
    # Test the vague query
    print("Testing: 'Analyze our ticket sales trends'")
    print("=" * 60)
    
    inputs = TicketingDataInputs(
        session_id="test-query-gen",
        tenant_id=TEST_TENANT_ID,
        user_id="test-user",
        query_request="Analyze our ticket sales trends",
        measures=[],  # Let LLM decide
        dimensions=[]  # Let LLM decide
    )
    
    try:
        result = await capability.execute(inputs)
        
        if queries_generated:
            query = queries_generated[0]
            
            # Check for dangerous patterns
            print("\n⚠️  WARNINGS:")
            if not query.get("limit"):
                print("  - No limit specified (could return millions of rows)")
            if not query.get("filters"):
                print("  - No filters (querying ALL data)")
            if "created_at_local" in str(query.get("dimensions", [])):
                print("  - Using created_at_local dimension (very high cardinality)")
            if len(query.get("dimensions", [])) > 1:
                print(f"  - Multiple dimensions ({len(query.get('dimensions', []))}) creates cartesian product")
                
    except Exception as e:
        print(f"\nError: {e}")

async def test_better_query():
    """Test a more specific query"""
    
    print("\n\nTesting: 'Show me monthly revenue trends for this year'")
    print("=" * 60)
    
    capability = TicketingDataCapability()
    
    # Same hook
    queries_generated = []
    original_execute_single = capability._execute_single_query
    
    async def capture_query(query, tenant_id):
        queries_generated.append(query)
        print("\n=== GENERATED QUERY ===")
        print(json.dumps(query, indent=2))
        return {"data": [], "total": 0}
    
    capability._execute_single_query = capture_query
    
    inputs = TicketingDataInputs(
        session_id="test-better-query",
        tenant_id=TEST_TENANT_ID,
        user_id="test-user",
        query_request="Show me monthly revenue trends for this year",
        measures=[],
        dimensions=[]
    )
    
    try:
        await capability.execute(inputs)
    except:
        pass

async def main():
    print("Query Generation Analysis")
    print("=" * 80)
    
    await test_query_generation()
    await test_better_query()

if __name__ == "__main__":
    asyncio.run(main())