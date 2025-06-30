#!/usr/bin/env python3
"""
Test queries with debugging for infinite loop issue

Run: python test_queries_debug.py
"""

import asyncio
import os
import sys
from workflow.graph import process_query

# Test queries grouped by complexity
SIMPLE_QUERIES = [
    "What is the total revenue for Gatsby?",
    "Show me revenue for Chicago",
    "How many tickets were sold for Hell's Kitchen?"
]

EMOTIONAL_QUERIES = [
    "I'm feeling overwhelmed with all these numbers",
    "This is stressful, help me understand what to focus on"
]

COMPLEX_QUERIES = [
    "Which shows need attention?",
    "How is Chicago performing?",
    "Compare sales for Hell's Kitchen and Chicago"
]

async def test_query_with_debug(query: str, max_wait: int = 30):
    """Test a single query with timeout and debugging"""
    print(f"\n{'='*60}")
    print(f"Testing: {query}")
    print(f"{'='*60}")
    
    try:
        # Add timeout to prevent infinite loops
        result = await asyncio.wait_for(
            process_query(
                query=query,
                session_id=f"test_{hash(query)}",
                user_id="test_user",
                tenant_id=os.getenv("TENANT_ID", "yesplan"),
                debug=True
            ),
            timeout=max_wait
        )
        
        print(f"✅ Success: {result['success']}")
        
        # Show trace to understand the flow
        if result.get('debug'):
            trace = result['debug'].get('trace_events', [])
            print("\nExecution trace:")
            for i, event in enumerate(trace):
                print(f"{i+1}. {event['event']} at {event.get('timestamp', 'N/A')}")
                
                # Show orchestration decisions
                if event['event'] == 'orchestration_decision':
                    data = event.get('data', {})
                    print(f"   Decision: {data.get('action')} - {data.get('capability', 'N/A')}")
                    if data.get('reason'):
                        print(f"   Reason: {data['reason']}")
        
        # Count orchestration loops
        orchestration_events = [e for e in trace if e['event'] == 'orchestration_decision']
        print(f"\nOrchestration loops: {len(orchestration_events)}")
        
        # Show final response
        messages = result.get('messages', [])
        if messages:
            last_assistant = next((m for m in reversed(messages) if m['role'] == 'assistant'), None)
            if last_assistant:
                print(f"\nFinal response: {last_assistant['content'][:200]}...")
        
        return True
        
    except asyncio.TimeoutError:
        print(f"❌ TIMEOUT after {max_wait} seconds - likely infinite loop!")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("🔍 Testing queries and debugging infinite loop issue")
    
    # Start with simplest query
    print("\n1️⃣ Testing SIMPLE query first:")
    success = await test_query_with_debug(SIMPLE_QUERIES[0])
    
    if not success:
        print("\n⚠️ Simple query failed - investigating loop issue")
        # Try with even shorter timeout to see pattern
        await test_query_with_debug(SIMPLE_QUERIES[0], max_wait=10)
        return
    
    # If simple worked, try emotional
    print("\n2️⃣ Testing EMOTIONAL query:")
    success = await test_query_with_debug(EMOTIONAL_QUERIES[0])
    
    if not success:
        print("\n⚠️ Emotional query failed")
        return
    
    # If those worked, try complex
    print("\n3️⃣ Testing COMPLEX query:")
    success = await test_query_with_debug(COMPLEX_QUERIES[0])
    
    print("\n✅ All test categories completed!")


if __name__ == "__main__":
    # Ensure we have required env vars
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        sys.exit(1)
    
    if not os.getenv("CUBE_API_TOKEN"):
        print("❌ Please set CUBE_API_TOKEN") 
        sys.exit(1)
    
    asyncio.run(main())