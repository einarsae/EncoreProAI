#!/usr/bin/env python3
"""
Test orchestrator with TicketingDataCapability

Run: docker-compose run --rm test python test_orchestrator_with_data.py
"""

import asyncio
import os
from workflow.graph import process_query

async def main():
    print("🎯 Testing Orchestrator with TicketingDataCapability")
    print("=" * 60)
    
    tenant_id = os.getenv("TENANT_ID", "test_tenant")
    
    # Test 1: Direct data query
    print("\n1️⃣ Test: Direct revenue query")
    result = await process_query(
        query="Show me revenue for Gatsby",
        session_id="test1",
        user_id="test_user",
        tenant_id=tenant_id,
        debug=True
    )
    
    print(f"Success: {result['success']}")
    messages = result.get('messages', [])
    
    # Show assistant responses
    for msg in messages:
        if msg['role'] == 'assistant':
            print(f"Assistant: {msg['content']}")
    
    # Show debug trace
    if result.get('debug'):
        trace = result['debug'].get('trace_events', [])
        print("\nTrace:")
        for event in trace:
            print(f"  - {event['event']}")
            if event['event'] == 'frames_extracted':
                frames = event['data'].get('frames', [])
                for frame in frames:
                    entities = [f"{e['text']} ({e['type']})" for e in frame.get('entities', [])]
                    print(f"    Frame: {frame.get('query')}")
                    print(f"    Entities: {entities}")
                    print(f"    Concepts: {frame.get('concepts', [])}")
    
    # Test 2: Complex query needing data
    print("\n\n2️⃣ Test: Top shows query")
    result = await process_query(
        query="What are my top 5 shows by revenue?",
        session_id="test2",
        user_id="test_user",
        tenant_id=tenant_id,
        debug=False
    )
    
    print(f"Success: {result['success']}")
    
    # Show only last assistant message
    messages = result.get('messages', [])
    assistant_messages = [msg for msg in messages if msg['role'] == 'assistant']
    if assistant_messages:
        print(f"Response: {assistant_messages[-1]['content']}")
    
    # Test 3: Mixed emotional and data query
    print("\n\n3️⃣ Test: Mixed emotional and data query")
    result = await process_query(
        query="I'm worried about Chicago. How is it performing?",
        session_id="test3",
        user_id="test_user",
        tenant_id=tenant_id,
        debug=True
    )
    
    print(f"Success: {result['success']}")
    
    # Count capabilities used
    if result.get('debug'):
        events = result['debug'].get('trace_events', [])
        capabilities_used = set()
        for event in events:
            if event['event'] == 'task_completed':
                capabilities_used.add(event['data'].get('capability'))
        
        print(f"Capabilities used: {', '.join(capabilities_used)}")
    
    # Show responses
    messages = result.get('messages', [])
    for msg in messages:
        if msg['role'] == 'assistant':
            print(f"Assistant: {msg['content'][:200]}...")
    
    # Test 4: Query requiring disambiguation
    print("\n\n4️⃣ Test: Ambiguous entity query")
    result = await process_query(
        query="Show me revenue for Paris",
        session_id="test4",
        user_id="test_user",
        tenant_id=tenant_id,
        debug=True
    )
    
    print(f"Success: {result['success']}")
    
    # Check if entity resolution found multiple candidates
    if result.get('debug'):
        events = result['debug'].get('trace_events', [])
        for event in events:
            if event['event'] == 'entities_resolved':
                entities = event['data'].get('entities', [])
                for entity in entities:
                    if len(entity.get('candidates', [])) > 1:
                        print(f"Ambiguous entity '{entity['text']}' has {len(entity['candidates'])} candidates")
    
    print("\n✅ Orchestrator test with data capability complete!")

if __name__ == "__main__":
    asyncio.run(main())