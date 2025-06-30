#!/usr/bin/env python3
"""
Test progressive analysis flow between EventAnalysisCapability and TicketingDataCapability

This tests whether EAC can:
1. Start with a general analysis request
2. Request specific data from TDC
3. Continue analysis with the fetched data
4. Potentially request more data for deeper insights
"""

import asyncio
import os
from datetime import datetime
import json
from workflow.graph import process_query
from workflow.nodes import WorkflowNodes

# Test configuration
TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"
TEST_USER_ID = "test-user-123"
TEST_SESSION_ID = f"progressive-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

async def test_simple_analysis():
    """Test a simple analysis that should complete in one pass"""
    print("\n1. Simple Analysis Test")
    print("=" * 60)
    print("Query: 'Tell me about our sales performance'")
    
    result = await process_query(
        query="Tell me about our sales performance",
        session_id=TEST_SESSION_ID,
        user_id=TEST_USER_ID,
        tenant_id=TEST_TENANT_ID,
        debug=True
    )
    
    print_result(result)
    return result

async def test_progressive_analysis():
    """Test analysis that requires multiple data fetches"""
    print("\n2. Progressive Analysis Test")
    print("=" * 60)
    print("Query: 'Analyze revenue trends and attendance patterns for our top shows'")
    
    result = await process_query(
        query="Analyze revenue trends and attendance patterns for our top shows",
        session_id=f"{TEST_SESSION_ID}-prog",
        user_id=TEST_USER_ID,
        tenant_id=TEST_TENANT_ID,
        debug=True
    )
    
    print_result(result)
    return result

async def test_complex_time_analysis():
    """Test complex time-based comparisons"""
    print("\n3. Complex Time Analysis Test")
    print("=" * 60)
    print("Query: 'Compare this month's performance to the same month last year, and identify which shows are trending up or down'")
    
    result = await process_query(
        query="Compare this month's performance to the same month last year, and identify which shows are trending up or down",
        session_id=f"{TEST_SESSION_ID}-time1",
        user_id=TEST_USER_ID,
        tenant_id=TEST_TENANT_ID,
        debug=True
    )
    
    print_result(result)
    return result

async def test_multi_period_analysis():
    """Test analysis across multiple time periods"""
    print("\n4. Multi-Period Analysis Test")
    print("=" * 60)
    print("Query: 'Show me quarterly trends for this year and compare weekend vs weekday performance'")
    
    result = await process_query(
        query="Show me quarterly trends for this year and compare weekend vs weekday performance",
        session_id=f"{TEST_SESSION_ID}-time2",
        user_id=TEST_USER_ID,
        tenant_id=TEST_TENANT_ID,
        debug=True
    )
    
    print_result(result)
    return result

async def test_seasonal_analysis():
    """Test seasonal pattern analysis"""
    print("\n5. Seasonal Pattern Analysis Test")
    print("=" * 60)
    print("Query: 'Analyze our holiday season performance compared to regular months and identify the best performing shows during peak times'")
    
    result = await process_query(
        query="Analyze our holiday season performance compared to regular months and identify the best performing shows during peak times",
        session_id=f"{TEST_SESSION_ID}-seasonal",
        user_id=TEST_USER_ID,
        tenant_id=TEST_TENANT_ID,
        debug=True
    )
    
    print_result(result)
    return result

def print_result(result):
    """Pretty print the result"""
    if result["success"]:
        print("\n✅ Success!")
        
        # Show final response
        if result.get("response"):
            response = result["response"]
            print(f"\nFinal Response:")
            print(f"  Message: {response.get('message', '')[:200]}...")
            if response.get("insights"):
                print(f"  Insights: {len(response['insights'])} insights")
                for i, insight in enumerate(response['insights'][:3], 1):
                    print(f"    {i}. {insight[:100]}...")
            if response.get("recommendations"):
                print(f"  Recommendations: {len(response['recommendations'])} recommendations")
                for i, rec in enumerate(response['recommendations'][:3], 1):
                    print(f"    {i}. {rec[:100]}...")
        
        # Analyze the execution flow
        if result.get("messages"):
            print("\nExecution Flow:")
            capabilities_used = []
            data_requests = []
            
            for msg in result["messages"]:
                if msg.get("role") == "system":
                    content = msg.get("content", "")
                    
                    # Track capability execution
                    if "Executing task" in content:
                        # Extract capability name
                        if ": " in content:
                            cap_part = content.split(": ")[1]
                            capabilities_used.append(cap_part)
                    
                    # Track data fetches
                    elif "Data fetched:" in content:
                        data_requests.append(content)
                    
                    # Track analysis completion
                    elif "Analysis complete:" in content:
                        print(f"    - Analysis: {content}")
            
            print(f"  Capabilities used: {' → '.join(capabilities_used)}")
            print(f"  Data requests: {len(data_requests)}")
            
            # Show debug info if available
            if result.get("debug") and result["debug"].get("trace_events"):
                events = result["debug"]["trace_events"]
                print(f"\nDebug Trace: {len(events)} events")
                for event in events[-5:]:  # Last 5 events
                    print(f"    - {event['event_type']}: {str(event.get('data', ''))[:100]}...")
    else:
        print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")

async def analyze_progressive_behavior():
    """Analyze how well the progressive analysis is working"""
    print("\n6. Progressive Behavior Analysis")
    print("=" * 60)
    
    # Test a query that explicitly asks for progressive analysis
    query = "First give me overall revenue for this quarter, then break it down by week and show me which venues are performing best"
    
    print(f"Query: '{query}'")
    
    result = await process_query(
        query=query,
        session_id=f"{TEST_SESSION_ID}-behavior",
        user_id=TEST_USER_ID,
        tenant_id=TEST_TENANT_ID,
        debug=True
    )
    
    # Detailed analysis of the flow
    if result.get("messages"):
        print("\nDetailed Flow Analysis:")
        
        task_count = 0
        for i, msg in enumerate(result["messages"]):
            if msg.get("role") == "system" and "Executing task" in msg.get("content", ""):
                task_count += 1
                print(f"\n  Task {task_count}:")
                print(f"    {msg['content']}")
                
                # Look for the task result
                for j in range(i+1, min(i+5, len(result["messages"]))):
                    next_msg = result["messages"][j]
                    if next_msg.get("role") == "system":
                        if "Data fetched:" in next_msg.get("content", ""):
                            print(f"    → Data: {next_msg['content']}")
                        elif "Analysis complete:" in next_msg.get("content", ""):
                            print(f"    → Analysis: {next_msg['content']}")
                        break

async def main():
    """Run all progressive analysis tests"""
    print("Testing Progressive Analysis Flow")
    print("=" * 80)
    print(f"Tenant: {TEST_TENANT_ID}")
    print(f"Session prefix: {TEST_SESSION_ID}")
    print("=" * 80)
    
    # Run tests - pick which ones to run
    results = []
    
    # Simple tests
    # results.append(await test_simple_analysis())
    # results.append(await test_progressive_analysis())
    
    # Complex time-based tests
    results.append(await test_complex_time_analysis())
    # results.append(await test_multi_period_analysis())
    # results.append(await test_seasonal_analysis())
    # results.append(await analyze_progressive_behavior())
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)
    
    successful = sum(1 for r in results if r["success"])
    print(f"✅ Successful: {successful}/{len(results)}")
    
    # Analyze progressive behavior
    print("\nProgressive Analysis Patterns:")
    for i, result in enumerate(results, 1):
        if result.get("messages"):
            cap_sequence = []
            for msg in result["messages"]:
                if msg.get("role") == "system" and "Executing task" in msg.get("content", ""):
                    content = msg["content"]
                    if ": " in content:
                        cap_sequence.append(content.split(": ")[1].split()[0])
            
            print(f"  Test {i}: {' → '.join(cap_sequence) if cap_sequence else 'No capabilities executed'}")

if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        exit(1)
    
    asyncio.run(main())