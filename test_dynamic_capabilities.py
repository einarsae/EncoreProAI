#!/usr/bin/env python3
"""
Test dynamic capability descriptions with real data
"""

import asyncio
import os
from datetime import datetime
from workflow.graph import process_query
from workflow.nodes import WorkflowNodes
from models.state import AgentState, CoreState

# Test configuration
TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"  # From actual database
TEST_USER_ID = "test-user-123"
TEST_SESSION_ID = f"test-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

async def test_capability_descriptions():
    """Test that each capability has a proper description"""
    print("1. Testing Capability Descriptions")
    print("=" * 60)
    
    nodes = WorkflowNodes()
    
    for name, cap in nodes.capabilities.items():
        desc = cap.describe()
        print(f"\n{name.upper()} Capability:")
        print(f"  Purpose: {desc.purpose}")
        print(f"  Inputs: {list(desc.inputs.keys())}")
        print(f"  Outputs: {list(desc.outputs.keys())}")
        print(f"  Examples: {len(desc.examples)} examples")

async def test_dynamic_context_building():
    """Test dynamic context generation"""
    print("\n\n2. Testing Dynamic Context Building")
    print("=" * 60)
    
    nodes = WorkflowNodes()
    
    # Create a state with a real query
    state = AgentState(
        core=CoreState(
            session_id=TEST_SESSION_ID,
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            query="What were Hamilton's ticket sales last month?"
        )
    )
    
    # Get the dynamic capabilities context
    capabilities_context = nodes._build_capabilities_context()
    print("\nDynamic Capabilities Context (first 500 chars):")
    print(capabilities_context[:500] + "...")

async def test_orchestration_with_capabilities():
    """Test full orchestration with dynamic capabilities"""
    print("\n\n3. Testing Full Orchestration Pipeline")
    print("=" * 60)
    
    test_queries = [
        "What's Hamilton's total revenue?",
        "Compare Hamilton and Chicago ticket sales last month",
        "I'm feeling overwhelmed by all this data",
        "Analyze trends for our top productions"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        
        try:
            result = await process_query(
                query=query,
                session_id=TEST_SESSION_ID,
                user_id=TEST_USER_ID,
                tenant_id=TEST_TENANT_ID,
                debug=True
            )
            
            if result["success"]:
                print(f"✅ Success!")
                if result.get("response"):
                    print(f"   Response: {result['response'].get('message', '')[:100]}...")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")

async def test_capability_execution_flow():
    """Test how capabilities are selected based on queries"""
    print("\n\n4. Testing Capability Selection Logic")
    print("=" * 60)
    
    # Test queries designed to trigger specific capabilities
    capability_tests = [
        ("I'm stressed about our sales", "chat"),
        ("Show me revenue for Hamilton", "ticketing_data"),
        ("Analyze attendance patterns", "event_analysis"),
        ("What are the trends for Chicago?", "ticketing_data + event_analysis")
    ]
    
    for query, expected in capability_tests:
        print(f"\nQuery: {query}")
        print(f"Expected: {expected}")
        
        result = await process_query(
            query=query,
            session_id=TEST_SESSION_ID,
            user_id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            debug=False
        )
        
        # Check which capabilities were used
        if result.get("messages"):
            capabilities_used = []
            for msg in result["messages"]:
                if msg.get("role") == "system" and "Executing task" in msg.get("content", ""):
                    # Extract capability name from system message
                    content = msg["content"]
                    if "execute_" in content:
                        cap_name = content.split("execute_")[1].split()[0]
                        capabilities_used.append(cap_name)
            
            print(f"Actual: {' + '.join(capabilities_used) if capabilities_used else 'none detected'}")

async def main():
    """Run all tests"""
    print("Testing Dynamic Capability Descriptions")
    print("=" * 80)
    print(f"Tenant: {TEST_TENANT_ID}")
    print(f"Session: {TEST_SESSION_ID}")
    print("=" * 80)
    
    await test_capability_descriptions()
    await test_dynamic_context_building()
    await test_orchestration_with_capabilities()
    await test_capability_execution_flow()
    
    print("\n\nAll tests complete!")

if __name__ == "__main__":
    # Ensure required environment variables are set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        exit(1)
    
    asyncio.run(main())