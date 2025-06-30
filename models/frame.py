"""
Simplified Frame Models - Minimal extraction for orchestrator-driven system

Focus on extracting only what needs resolution:
- Entities that need database lookup
- Time expressions that need parsing  
- Concepts that might have memory context
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


# Base resolution models
class DateRange(BaseModel):
    """Parsed time expression"""
    start: datetime
    end: datetime
    original_text: str
    is_relative: bool = False


class MemoryContext(BaseModel):
    """Context retrieved from memory for a concept"""
    concept: str
    related_queries: List[str] = Field(default_factory=list)
    usage_count: int = 0
    last_seen: Optional[datetime] = None
    relevance_score: float = Field(ge=0.0, le=1.0)


# Entity to resolve from frame extraction
class EntityToResolve(BaseModel):
    """Entity extracted from query that needs resolution"""
    id: str  # Simple ID from extractor: "e1", "e2"
    text: str  # e.g., "Chicago"
    type: str  # Guessed type: "production", "city", "venue"


# Resolution result models with id, text, and specific resolution data
class ResolvedEntity(BaseModel):
    """Resolved entity with candidates"""
    id: str  # Simple ID: "e1", "e2"
    entity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Persistent UUID
    text: str  # e.g., "Chicago"
    type: str  # Entity type used for resolution
    candidates: List['EntityCandidate']


class ResolvedConcept(BaseModel):
    """Resolved concept with memory context"""
    id: str  # Simple ID: "c1", "c2"
    concept_id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Persistent UUID
    text: str  # e.g., "revenue", "overwhelmed"
    memory_context: MemoryContext


class Frame(BaseModel):
    """Simplified frame - just what needs resolution"""
    # Dual ID system
    id: str = Field(..., description="Simple ID from extractor (f1, f2)")
    frame_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Persistent UUID")
    
    # Session tracking
    session_id: Optional[str] = Field(None, description="Links to conversation session")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Content
    query: str = Field(..., description="Original text for this semantic unit")
    
    # Things to resolve (these ARE part of the frame!)
    entities: List[EntityToResolve] = Field(default_factory=list, description="Entities to resolve")
    concepts: List[str] = Field(default_factory=list, description="Concepts for memory lookup")
    
    # Resolutions (populated after extraction)
    resolved_entities: List[ResolvedEntity] = Field(default_factory=list)
    resolved_concepts: List[ResolvedConcept] = Field(default_factory=list)
    
    def needs_resolution(self) -> bool:
        """Check if frame has anything to resolve"""
        return bool(self.entities or self.concepts)
    
    def is_resolved(self) -> bool:
        """Check if all resolutions are complete"""
        # Check all entities have resolutions
        entity_ids = {e.id for e in self.entities}
        resolved_entity_ids = {r.id for r in self.resolved_entities}
        entities_resolved = entity_ids <= resolved_entity_ids
        
        # Concepts are optional - memory might not have context
        return entities_resolved
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "What is the revenue for Chicago last month?",
                "entities": ["Chicago"],
                "times": ["last month"],
                "concepts": ["revenue"],
                "resolved_entities": [
                    {
                        "id": "e1",
                        "text": "Chicago",
                        "candidates": []
                    }
                ],
                "resolved_times": [
                    {
                        "id": "t1",
                        "text": "last month",
                        "date_range": {
                            "start": "2024-01-01T00:00:00",
                            "end": "2024-01-31T23:59:59",
                            "original_text": "last month",
                            "is_relative": True
                        }
                    }
                ],
                "resolved_concepts": []
            }
        }
    }


# Import EntityCandidate from entity_resolver instead of defining it here
from services.entity_resolver import EntityCandidate

# Forward reference resolution
ResolvedEntity.model_rebuild()