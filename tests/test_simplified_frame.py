"""
Tests for Simplified Frame Models

This file tests:
- Frame model with entities, times, concepts lists
- ResolvedEntity, ResolvedTime, ResolvedConcept models
- Frame resolution tracking
- Serialization and validation

Run: docker-compose run --rm test python -m pytest tests/test_simplified_frame.py -v
Run specific test: docker-compose run --rm test python -m pytest tests/test_simplified_frame.py::test_frame_creation -v
"""

import pytest
from datetime import datetime
from typing import List

from models.frame import (
    Frame, EntityToResolve, ResolvedEntity, ResolvedConcept,
    DateRange, MemoryContext, EntityCandidate
)


@pytest.mark.unit
def test_frame_creation():
    """Test creating a simplified frame"""
    entities = [EntityToResolve(id="e1", text="Chicago", type="production")]
    
    frame = Frame(
        id="f1",
        query="What is the revenue for Chicago last month?",
        entities=entities,
        concepts=["revenue"]
    )
    
    assert frame.query == "What is the revenue for Chicago last month?"
    assert len(frame.entities) == 1
    assert frame.entities[0].text == "Chicago"
    assert frame.entities[0].type == "production" 
    assert frame.concepts == ["revenue"]
    assert frame.needs_resolution() == True
    assert frame.is_resolved() == False


@pytest.mark.unit
def test_frame_with_resolutions():
    """Test frame with resolved entities and concepts"""
    
    # Create frame
    entities = [EntityToResolve(id="e1", text="Chicago", type="production")]
    frame = Frame(
        id="f1",
        query="Show me Chicago revenue last month",
        entities=entities,
        concepts=["revenue"]
    )
    
    # Add entity resolution
    chicago_candidates = [
        EntityCandidate(
            entity_type="production",
            id="prod_123",
            name="Chicago",
            score=0.95,
            disambiguation="Chicago (Broadway)",
            sold_last_30_days=1500
        ),
        EntityCandidate(
            entity_type="production", 
            id="prod_456",
            name="Chicago",
            score=0.90,
            disambiguation="Chicago (Tour)",
            sold_last_30_days=800
        )
    ]
    
    frame.resolved_entities.append(
        ResolvedEntity(
            id="e1",
            text="Chicago",
            type="production",
            candidates=chicago_candidates
        )
    )
    
    # Add concept resolution
    frame.resolved_concepts.append(
        ResolvedConcept(
            id="c1",
            text="revenue",
            memory_context=MemoryContext(
                concept="revenue",
                related_queries=["show revenue", "total sales"],
                usage_count=42,
                relevance_score=0.85
            )
        )
    )
    
    # Test resolution status
    assert frame.is_resolved() == True
    assert len(frame.resolved_entities) == 1
    assert len(frame.resolved_entities[0].candidates) == 2
    assert frame.resolved_entities[0].candidates[0].disambiguation == "Chicago (Broadway)"


@pytest.mark.unit
def test_frame_serialization():
    """Test frame serialization to JSON"""
    entities = [
        EntityToResolve(id="e1", text="Chicago", type="city"),
        EntityToResolve(id="e2", text="Chicago", type="production")
    ]
    
    frame = Frame(
        id="f1",
        query="How many people from Chicago saw Chicago?",
        entities=entities,
        concepts=["people"]
    )
    
    # Test serialization
    frame_dict = frame.model_dump(mode='json')
    
    assert frame_dict['query'] == "How many people from Chicago saw Chicago?"
    assert len(frame_dict['entities']) == 2
    assert frame_dict['concepts'] == ["people"]
    
    # Test deserialization
    frame_restored = Frame.model_validate(frame_dict)
    assert frame_restored.query == frame.query
    assert len(frame_restored.entities) == 2


@pytest.mark.unit
def test_emotional_concepts():
    """Test that emotional words are treated as concepts"""
    frame = Frame(
        id="f1",
        query="I'm feeling overwhelmed with these numbers",
        entities=[],
        concepts=["overwhelmed", "numbers"]
    )
    
    assert "overwhelmed" in frame.concepts
    assert frame.needs_resolution() == True


@pytest.mark.unit
def test_multiple_frames():
    """Test handling multiple frames for unrelated content"""
    frames = [
        Frame(
            id="f1",
            query="How many people saw Chicago last Saturday",
            entities=[EntityToResolve(id="e1", text="Chicago", type="production")],
            concepts=["people"]
        ),
        Frame(
            id="f2",
            query="Also, can you send me weekly revenue report",
            entities=[],
            concepts=["weekly", "revenue", "report", "automation"]
        )
    ]
    
    assert len(frames) == 2
    assert len(frames[0].entities) == 1
    assert frames[0].entities[0].text == "Chicago"
    assert "automation" in frames[1].concepts


@pytest.mark.unit
def test_complex_connected_frame():
    """Test single frame for connected content"""
    # All Chicago-related questions stay in one frame
    entities = [
        EntityToResolve(id="e1", text="Chicago", type="production"),
        EntityToResolve(id="e2", text="Chicago", type="city"),
        EntityToResolve(id="e3", text="Chicago", type="city")
    ]
    
    frame = Frame(
        id="f1",
        query="How many people saw Chicago last Saturday. How many were from Chicago. What was the core audience and who should I be targeting for that show. How has the weather been in Chicago. Is that related.",
        entities=entities,
        concepts=["people", "audience", "targeting", "segmentation", "weather", "analysis"]
    )
    
    assert len(frame.entities) == 3  # Three mentions of Chicago
    assert "weather" in frame.concepts  # Weather is a concept here
    assert "segmentation" in frame.concepts
    assert frame.needs_resolution() == True


@pytest.mark.unit 
def test_partial_resolution():
    """Test frame with only some items resolved"""
    entities = [
        EntityToResolve(id="e1", text="Chicago", type="production"),
        EntityToResolve(id="e2", text="Hamilton", type="production")
    ]
    
    frame = Frame(
        id="f1",
        query="Revenue for Chicago and Hamilton",
        entities=entities,
        concepts=["revenue"]
    )
    
    # Only resolve Chicago
    frame.resolved_entities.append(
        ResolvedEntity(
            id="e1",
            text="Chicago",
            type="production",
            candidates=[
                EntityCandidate(
                    entity_type="production",
                    id="prod_123",
                    name="Chicago",
                    score=0.95,
                    disambiguation="Chicago (Broadway)"
                )
            ]
        )
    )
    
    # Hamilton not resolved yet
    assert frame.is_resolved() == False
    
    # Now resolve Hamilton
    frame.resolved_entities.append(
        ResolvedEntity(
            id="e2",
            text="Hamilton",
            type="production",
            candidates=[
                EntityCandidate(
                    entity_type="production",
                    id="prod_789",
                    name="Hamilton",
                    score=1.0,
                    disambiguation="Hamilton (Broadway)"
                )
            ]
        )
    )
    
    # Now fully resolved
    assert frame.is_resolved() == True