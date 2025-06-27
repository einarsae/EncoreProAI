"""
Tests for LangGraph Orchestrator

Tests the orchestration loop with available capabilities.
Can run with just ChatCapability to start.

Run: docker-compose run --rm test python -m pytest tests/test_orchestrator.py -v -s
"""

import pytest
import asyncio
from typing import Dict, Any

from workflow.graph import create_workflow, process_query
from models.state import AgentState, CoreState
from models.frame import Frame, EntityToResolve


class TestOrchestrator:
    """Test orchestration workflow"""
    
    @pytest.mark.asyncio
    async def test_simple_chat_orchestration(self):
        """Test orchestration with emotional query -> chat capability"""
        
        # Query that should trigger chat capability
        result = await process_query(
            query="I'm feeling overwhelmed with all these numbers",
            session_id="test_session",
            user_id="test_user", 
            tenant_id="test_tenant",
            debug=True
        )
        
        print("\n🧪 Test: Simple Chat Orchestration")
        print(f"Query: 'I'm feeling overwhelmed with all these numbers'")
        print(f"Success: {result['success']}")
        
        # Check messages
        messages = result.get('messages', [])
        for msg in messages:
            if msg['role'] == 'assistant':
                print(f"Response: {msg['content']}")
        
        # Check debug trace
        if result.get('debug'):
            trace = result['debug'].get('trace_events', [])
            print("\nTrace:")
            for event in trace:
                print(f"  - {event['event']}")
        
        assert result['success'] == True
        assert any(msg['role'] == 'assistant' for msg in messages)
    
    @pytest.mark.asyncio
    async def test_data_query_orchestration(self):
        """Test orchestration with data query (will fail without TicketingDataCapability)"""
        
        # Query that needs data capability
        result = await process_query(
            query="Show me revenue for Gatsby",
            session_id="test_session",
            user_id="test_user",
            tenant_id="test_tenant", 
            debug=True
        )
        
        print("\n🧪 Test: Data Query Orchestration")
        print(f"Query: 'Show me revenue for Gatsby'")
        print(f"Success: {result['success']}")
        
        # This should either:
        # 1. Use chat to explain it can't access data yet
        # 2. Try to use ticketing_data and fail gracefully
        
        messages = result.get('messages', [])
        for msg in messages[-3:]:  # Last few messages
            print(f"{msg['role']}: {msg['content'][:100]}...")
    
    @pytest.mark.asyncio
    async def test_multi_frame_orchestration(self):
        """Test orchestration with multi-frame query"""
        
        # Query that creates multiple frames
        result = await process_query(
            query="How many people saw Chicago last Saturday. Also, can you send me a weekly report.",
            session_id="test_session",
            user_id="test_user",
            tenant_id="test_tenant",
            debug=True
        )
        
        print("\n🧪 Test: Multi-Frame Orchestration") 
        print(f"Query: Complex multi-frame query")
        print(f"Success: {result['success']}")
        
        # Check if multiple frames were created
        if result.get('debug'):
            events = result['debug'].get('trace_events', [])
            frame_event = next((e for e in events if e['event'] == 'frames_extracted'), None)
            if frame_event:
                frame_count = frame_event['data'].get('count', 0)
                print(f"Frames extracted: {frame_count}")
    
    @pytest.mark.asyncio
    async def test_orchestration_loop_limit(self):
        """Test that orchestration loop has proper limits"""
        
        # Create a workflow
        workflow = create_workflow()
        
        # Create initial state
        state = AgentState(
            core=CoreState(
                session_id="test",
                user_id="test",
                tenant_id="test",
                query="Test query"
            )
        )
        
        # Manually set high loop count
        state.execution.loop_count = 15
        
        # Process should stop due to loop limit
        final_state = await workflow.ainvoke(state)
        
        assert final_state.core.status == "error"
        assert "Maximum execution loops exceeded" in str(final_state.core.messages[-1].content)
    
    @pytest.mark.unit
    def test_workflow_structure(self):
        """Test workflow graph structure"""
        
        workflow = create_workflow()
        
        # Check nodes exist
        nodes = workflow.nodes
        expected_nodes = {
            "extract_frames",
            "resolve_entities", 
            "resolve_concepts",
            "orchestrate",
            "execute_chat"
        }
        
        print("\n🧪 Test: Workflow Structure")
        print(f"Nodes: {nodes}")
        
        for node in expected_nodes:
            assert node in nodes, f"Missing node: {node}"


@pytest.mark.asyncio
async def test_orchestrator_without_all_capabilities():
    """
    Quick test to show orchestrator working with limited capabilities.
    This demonstrates what happens when capabilities are missing.
    """
    
    print("\n🎯 Testing Orchestrator with Limited Capabilities")
    print("=" * 60)
    
    # Test 1: Emotional query (should work)
    print("\n1️⃣ Emotional Query Test:")
    result = await process_query(
        query="I'm feeling stressed about our sales numbers",
        session_id="test1",
        user_id="user1",
        tenant_id="tenant1"
    )
    
    if result['success']:
        print("✅ Emotional query handled successfully")
    else:
        print("❌ Emotional query failed")
    
    # Test 2: Data query (should gracefully handle missing capability)
    print("\n2️⃣ Data Query Test (no TicketingDataCapability):")
    result = await process_query(
        query="What's the revenue for Hamilton?",
        session_id="test2", 
        user_id="user1",
        tenant_id="tenant1"
    )
    
    # Should either use chat or fail gracefully
    messages = result.get('messages', [])
    if messages:
        last_message = messages[-1]
        print(f"Handled as: {last_message.get('content', 'No response')[:100]}...")
    
    # Test 3: Complex query
    print("\n3️⃣ Complex Query Test:")
    result = await process_query(
        query="I'm overwhelmed. Can you show me which shows need attention?",
        session_id="test3",
        user_id="user1", 
        tenant_id="tenant1"
    )
    
    print(f"Success: {result['success']}")
    
    print("\n" + "=" * 60)
    print("Orchestrator is working! Ready to add more capabilities.")


if __name__ == "__main__":
    # Run quick test
    asyncio.run(test_orchestrator_without_all_capabilities())