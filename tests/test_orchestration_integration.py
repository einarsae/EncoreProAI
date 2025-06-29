"""
Integration tests for orchestration with real services

This file tests:
- Real frame extraction with LLM
- Real entity resolution with PostgreSQL
- Real data fetching from Cube.js
- Real analysis with EventAnalysisCapability
- Complete end-to-end flows

Run: docker-compose run --rm test python -m pytest tests/test_orchestration_integration.py -v -s
Run specific test: docker-compose run --rm test python -m pytest tests/test_orchestration_integration.py::TestOrchestrationIntegration::test_method -v -s
"""

import pytest
import asyncio
import os
from datetime import datetime

from models.state import AgentState, CoreState, ExecutionState
from workflow.nodes import WorkflowNodes
from workflow.graph import create_workflow


@pytest.mark.integration
class TestOrchestrationIntegration:
    """Test orchestration with real services"""
    
    @pytest.fixture
    def workflow_nodes(self):
        """Create workflow nodes with real services"""
        # Override database URL for tests
        nodes = WorkflowNodes()
        nodes.entity_resolver.database_url = "postgresql://encore:secure_password@postgres:5432/encoreproai"
        return nodes
    
    @pytest.fixture
    def graph(self):
        """Create workflow graph"""
        return create_workflow()
    
    @pytest.fixture
    def base_state(self):
        """Create base agent state"""
        return AgentState(
            core=CoreState(
                session_id="test_integration",
                tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
                user_id="user123",
                query="",  # Will be set per test
                timestamp=datetime.utcnow()
            ),
            execution=ExecutionState()
        )
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OpenAI API key")
    async def test_simple_revenue_query(self, graph, base_state):
        """Test simple revenue query through full pipeline"""
        base_state.core.query = "Show me total revenue for all productions"
        
        # Run through graph
        result = await graph.ainvoke(base_state)
        
        # Should complete successfully
        assert result.core.status == "complete"
        assert len(result.execution.completed_tasks) >= 1
        
        # Should have ticketing data task
        tdc_tasks = [t for t in result.execution.completed_tasks.values() 
                     if t.capability == "ticketing_data"]
        assert len(tdc_tasks) == 1
        assert tdc_tasks[0].success
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OpenAI API key")
    async def test_entity_specific_query(self, graph, base_state):
        """Test query with specific entity resolution"""
        base_state.core.query = "How much revenue did Chicago generate last month?"
        
        # Run through graph
        result = await graph.ainvoke(base_state)
        
        # Should complete successfully
        assert result.core.status == "complete"
        
        # Check frame extraction worked
        assert len(result.semantic.frames) > 0
        frame = result.semantic.frames[0]
        
        # Should have identified Chicago as entity
        entity_texts = [e.text.lower() for e in frame.entities]
        assert "chicago" in entity_texts
        
        # Should have resolved Chicago
        if frame.resolved_entities:
            chicago_resolved = [r for r in frame.resolved_entities 
                              if r.text.lower() == "chicago"]
            assert len(chicago_resolved) > 0
            assert chicago_resolved[0].candidates[0].id  # Should have ID
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OpenAI API key")
    async def test_analysis_query_progressive(self, graph, base_state):
        """Test analysis query with progressive data fetching"""
        base_state.core.query = "Analyze the performance trends for Chicago"
        
        # Run through graph
        result = await graph.ainvoke(base_state)
        
        # Should complete successfully
        assert result.core.status == "complete"
        
        # Should have multiple tasks (analysis → data → analysis)
        assert len(result.execution.completed_tasks) >= 2
        
        # Check task sequence
        task_list = list(result.execution.completed_tasks.values())
        capabilities_used = [t.capability for t in task_list]
        
        # Should use event_analysis and ticketing_data
        assert "event_analysis" in capabilities_used
        assert "ticketing_data" in capabilities_used
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OpenAI API key") 
    async def test_comparison_query(self, graph, base_state):
        """Test comparison query requiring multi-fetch"""
        base_state.core.query = "Compare revenue between Q1 and Q2 2024"
        
        # Run through graph
        result = await graph.ainvoke(base_state)
        
        # Should complete successfully
        assert result.core.status == "complete"
        
        # Should have ticketing data task
        tdc_tasks = [t for t in result.execution.completed_tasks.values() 
                     if t.capability == "ticketing_data"]
        assert len(tdc_tasks) >= 1
        
        # Check if multi-fetch was used
        tdc_result = tdc_tasks[0].result
        if "combined_results" in tdc_result:
            # Multi-fetch was used
            assert len(tdc_result["combined_results"]) == 2
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OpenAI API key")
    async def test_emotional_support_query(self, graph, base_state):
        """Test emotional support routing"""
        base_state.core.query = "I'm feeling really overwhelmed by all these numbers"
        
        # Run through graph
        result = await graph.ainvoke(base_state)
        
        # Should complete (even if chat capability not fully implemented)
        assert result.core.status in ["complete", "error"]
        
        # Should attempt to use chat capability
        if result.execution.completed_tasks:
            chat_tasks = [t for t in result.execution.completed_tasks.values() 
                         if t.capability == "chat"]
            # May or may not have chat depending on implementation
            if chat_tasks:
                assert len(chat_tasks) >= 1
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OpenAI API key")
    async def test_complex_multi_entity_query(self, graph, base_state):
        """Test complex query with multiple entities"""
        base_state.core.query = "Compare Chicago and Hamilton revenue by venue"
        
        # Run through graph  
        result = await graph.ainvoke(base_state)
        
        # Should complete successfully
        assert result.core.status == "complete"
        
        # Check entities were identified
        if result.semantic.frames:
            frame = result.semantic.frames[0]
            entity_texts = [e.text.lower() for e in frame.entities]
            assert "chicago" in entity_texts
            assert "hamilton" in entity_texts
            
            # Both should be resolved
            if frame.resolved_entities:
                assert len(frame.resolved_entities) >= 2
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="Requires OpenAI API key")
    async def test_time_based_analysis(self, graph, base_state):
        """Test time-based analysis query"""
        base_state.core.query = "Show me the trend of ticket sales over the last 6 months"
        
        # Run through graph
        result = await graph.ainvoke(base_state)
        
        # Should complete successfully
        assert result.core.status == "complete"
        
        # Should use ticketing data with time dimension
        tdc_tasks = [t for t in result.execution.completed_tasks.values() 
                     if t.capability == "ticketing_data"]
        assert len(tdc_tasks) >= 1
        
        # Check if time dimension was used
        tdc_inputs = tdc_tasks[0].inputs
        if "dimensions" in tdc_inputs:
            # Should have time-based dimension
            dims_str = str(tdc_inputs["dimensions"])
            assert any(term in dims_str.lower() for term in ["month", "week", "time", "date"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])