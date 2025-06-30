#!/usr/bin/env python3
"""
Test actual orchestrator routing decisions
"""

import asyncio
import os
import json
from workflow.nodes import WorkflowNodes
from models.state import AgentState, CoreState

TEST_TENANT_ID = "5465f607-b975-4c80-bed1-a1a5a3c779e2"

async def test_routing(query: str):
    """Test where orchestrator routes a query"""
    
    nodes = WorkflowNodes()
    
    # Create state with the query
    state = AgentState(
        core=CoreState(
            session_id="test-routing",
            user_id="test-user",
            tenant_id=TEST_TENANT_ID,
            query=query
        )
    )
    
    # Build context
    context = nodes._build_orchestration_context(state)
    
    # Get decision
    decision = await nodes._get_orchestration_decision(context)
    
    return {
        "query": query,
        "capability": decision.capability,
        "action": decision.action
    }

async def main():
    print("Testing Orchestrator Routing Decisions")
    print("=" * 80)
    
    test_queries = [
        # Analysis queries - should go to event_analysis
        "Analyze our ticket sales trends",
        "What patterns do you see in our sales?",
        "Compare this month to last month",
        "Show me trends over time",
        "How are we performing?",
        
        # Data queries - should go to ticketing_data
        "Show me revenue for last month",
        "Get attendance numbers for Chicago",
        "Revenue for all shows this year",
        "Top 5 productions by sales",
        
        # Emotional queries - should go to chat
        "I'm overwhelmed by these numbers",
        "This is confusing, help me understand",
        "I'm stressed about our performance",
        
        # Ambiguous queries
        "Tell me about Chicago",
        "What's happening with our shows?"
    ]
    
    results = []
    for query in test_queries:
        result = await test_routing(query)
        results.append(result)
    
    # Print results grouped by expected routing
    print("\nANALYSIS QUERIES (should → event_analysis):")
    print("-" * 60)
    for r in results[:5]:
        status = "✅" if r["capability"] == "event_analysis" else "❌"
        print(f"{status} '{r['query']}' → {r['capability']}")
    
    print("\nDATA QUERIES (should → ticketing_data):")
    print("-" * 60)
    for r in results[5:9]:
        status = "✅" if r["capability"] == "ticketing_data" else "❌"
        print(f"{status} '{r['query']}' → {r['capability']}")
    
    print("\nEMOTIONAL QUERIES (should → chat):")
    print("-" * 60)
    for r in results[9:12]:
        status = "✅" if r["capability"] == "chat" else "❌"
        print(f"{status} '{r['query']}' → {r['capability']}")
    
    print("\nAMBIGUOUS QUERIES:")
    print("-" * 60)
    for r in results[12:]:
        print(f"'{r['query']}' → {r['capability']}")

if __name__ == "__main__":
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set")
        exit(1)
    
    asyncio.run(main())