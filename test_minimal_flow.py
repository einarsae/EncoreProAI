"""Minimal test of Chicago revenue query"""

import asyncio
from workflow.graph import process_query

async def test_minimal():
    """Test minimal Chicago query"""
    result = await process_query(
        query="What is the revenue for Chicago?",
        session_id="test-session",
        user_id="test-user",
        tenant_id="5465f607-b975-4c80-bed1-a1a5a3c779e2"  # Real tenant from DB
    )
    
    print(f"Success: {result['success']}")
    if result.get('response'):
        print(f"Response: {result['response'].get('message', 'No message')[:200]}...")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    # Show any system messages
    if result.get('messages'):
        print("\nSystem messages:")
        for msg in result['messages'][-5:]:  # Last 5 messages
            if msg.get('role') == 'system':
                print(f"  - {msg.get('content', '')[:100]}...")

if __name__ == "__main__":
    asyncio.run(test_minimal())