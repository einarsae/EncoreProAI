#!/usr/bin/env python3
"""
Test simple progressive analysis flow
"""

import asyncio
import os
from datetime import datetime
from workflow.graph import process_query

# Test configuration
TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"
TEST_USER_ID = "test-user-123"
TEST_SESSION_ID = f"simple-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

async def test_basic_flow():
    """Test basic progressive flow"""
    print("\nTest: Basic Progressive Analysis")
    print("=" * 60)
    
    # Start with a general request that should trigger analysis
    query = "Analyze our ticket sales trends"
    print(f"Query: '{query}'")
    
    result = await process_query(
        query=query,
        session_id=TEST_SESSION_ID,
        user_id=TEST_USER_ID,
        tenant_id=TEST_TENANT_ID,
        debug=True
    )
    
    # Analyze the flow
    if result["success"]:
        print("\n✅ Success!")
        
        # Track capability sequence
        capabilities = []
        for msg in result.get("messages", []):
            if msg.get("role") == "system" and "Executing task" in msg.get("content", ""):
                content = msg["content"]
                # Extract capability name
                parts = content.split(": ")
                if len(parts) > 1:
                    cap_name = parts[1].split()[0]
                    capabilities.append(cap_name)
        
        print(f"\nCapability Flow: {' → '.join(capabilities)}")
        
        # Show final response
        if result.get("response"):
            resp = result["response"]
            print(f"\nFinal Response:")
            print(f"  Message: {resp.get('message', '')[:150]}...")
            print(f"  Insights: {len(resp.get('insights', []))}")
            print(f"  Recommendations: {len(resp.get('recommendations', []))}")
            
            # Show first insight
            if resp.get("insights"):
                print(f"\nFirst Insight: {resp['insights'][0][:150]}...")
    else:
        print(f"\n❌ Failed: {result.get('error', 'Unknown')}")
        
        # Show last few messages for debugging
        if result.get("messages"):
            print("\nLast few messages:")
            for msg in result["messages"][-5:]:
                print(f"  {msg.get('role')}: {msg.get('content', '')[:100]}...")

async def test_explicit_progressive():
    """Test explicit progressive request"""
    print("\n\nTest: Explicit Progressive Request")
    print("=" * 60)
    
    query = "First show me total revenue this month, then analyze which shows are performing best"
    print(f"Query: '{query}'")
    
    result = await process_query(
        query=query,
        session_id=f"{TEST_SESSION_ID}-explicit",
        user_id=TEST_USER_ID,
        tenant_id=TEST_TENANT_ID,
        debug=False  # Less verbose
    )
    
    if result["success"]:
        print("\n✅ Success!")
        
        # Count tasks
        task_count = 0
        for msg in result.get("messages", []):
            if msg.get("role") == "system" and "Executing task" in msg.get("content", ""):
                task_count += 1
                print(f"\nTask {task_count}: {msg['content']}")
    else:
        print(f"\n❌ Failed: {result.get('error', 'Unknown')}")

async def test_analysis_needing_data():
    """Test analysis that explicitly needs data"""
    print("\n\nTest: Analysis Requiring Data")
    print("=" * 60)
    
    query = "What patterns do you see in our weekend vs weekday sales?"
    print(f"Query: '{query}'")
    
    result = await process_query(
        query=query,
        session_id=f"{TEST_SESSION_ID}-patterns",
        user_id=TEST_USER_ID,
        tenant_id=TEST_TENANT_ID,
        debug=False
    )
    
    if result["success"]:
        print("\n✅ Success!")
        
        # Show capability flow
        capabilities = []
        for msg in result.get("messages", []):
            if msg.get("role") == "system" and "Executing task" in msg.get("content", ""):
                content = msg["content"]
                if ": " in content:
                    cap_name = content.split(": ")[1].split()[0]
                    capabilities.append(cap_name)
        
        print(f"\nCapability Flow: {' → '.join(capabilities)}")
        
        # Check if it went to ticketing_data first or event_analysis
        if capabilities:
            print(f"\nFirst capability: {capabilities[0]}")
            print("(Should ideally be event_analysis that then requests data)")
    else:
        print(f"\n❌ Failed: {result.get('error', 'Unknown')}")

async def main():
    """Run all tests"""
    print("Testing Simple Progressive Analysis")
    print("=" * 80)
    print(f"Tenant: {TEST_TENANT_ID}")
    print("=" * 80)
    
    await test_basic_flow()
    # await test_explicit_progressive()
    # await test_analysis_needing_data()
    
    print("\n\nAll tests complete!")

if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        exit(1)
    
    asyncio.run(main())