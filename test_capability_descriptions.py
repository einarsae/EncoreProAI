#!/usr/bin/env python3
"""
Review capability descriptions as seen by orchestrator
"""

import asyncio
from workflow.nodes import WorkflowNodes

async def review_descriptions():
    """Review how capabilities describe themselves"""
    
    nodes = WorkflowNodes()
    
    print("CAPABILITY DESCRIPTIONS AS SEEN BY ORCHESTRATOR")
    print("=" * 80)
    
    # Get the dynamic context
    capabilities_context = nodes._build_capabilities_context()
    print(capabilities_context)
    
    print("\n" + "=" * 80)
    print("ANALYSIS OF DESCRIPTIONS")
    print("=" * 80)
    
    # Check each capability
    for name, cap in nodes.capabilities.items():
        desc = cap.describe()
        print(f"\n{name.upper()}:")
        print(f"  Purpose: {desc.purpose}")
        
        # Analyze purpose for routing clues
        purpose_lower = desc.purpose.lower()
        
        print("\n  Routing indicators in purpose:")
        if "raw" in purpose_lower or "fetch" in purpose_lower:
            print("    ✓ Indicates data fetching")
        if "analysis" in purpose_lower or "analyze" in purpose_lower:
            print("    ✓ Indicates analysis")
        if "trend" in purpose_lower or "pattern" in purpose_lower:
            print("    ✓ Indicates pattern recognition")
        if "emotion" in purpose_lower or "support" in purpose_lower:
            print("    ✓ Indicates emotional support")
            
        # Check examples
        print(f"\n  Examples ({len(desc.examples)}):")
        for ex in desc.examples[:3]:
            print(f"    - {ex}")
            
        # Look for routing conflicts
        if name == "ticketing_data":
            if any("analyze" in ex.lower() or "trend" in ex.lower() for ex in desc.examples):
                print("    ⚠️  WARNING: Examples include analysis terms!")
        
        if name == "event_analysis":
            if any("raw" in ex.lower() or "fetch" in ex.lower() for ex in desc.examples):
                print("    ⚠️  WARNING: Examples include data fetching terms!")

async def test_routing_decisions():
    """Test how different queries would be routed"""
    
    print("\n\n" + "=" * 80)
    print("ROUTING DECISION TESTS")
    print("=" * 80)
    
    test_queries = [
        "Analyze our ticket sales trends",
        "Show me revenue for last month",
        "What patterns do you see in our data?",
        "Get attendance numbers for Chicago",
        "I'm overwhelmed by these numbers",
        "Compare this month to last month",
        "How are we doing?",
        "Fetch all production data"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        query_lower = query.lower()
        
        # Simple heuristic based on keywords
        if any(word in query_lower for word in ["analyze", "pattern", "trend", "compare", "how"]):
            print("  → Should route to: event_analysis")
        elif any(word in query_lower for word in ["show", "get", "fetch", "revenue", "attendance", "numbers"]):
            print("  → Should route to: ticketing_data")
        elif any(word in query_lower for word in ["overwhelmed", "stressed", "help"]):
            print("  → Should route to: chat")
        else:
            print("  → Unclear routing")

async def main():
    await review_descriptions()
    await test_routing_decisions()

if __name__ == "__main__":
    asyncio.run(main())