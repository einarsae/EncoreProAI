"""
Capability input/output models for type-safe capability execution
Each capability has specific input and output models for validation
"""

from typing import Dict, List, Optional, Any, Literal, Union
from pydantic import BaseModel, Field, model_validator
from datetime import datetime

from models.state import Message


class CapabilityInputs(BaseModel):
    """Base class for all capability inputs"""
    session_id: str
    tenant_id: str
    user_id: str


class CapabilityResult(BaseModel):
    """Base class for all capability results"""
    success: bool = True
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# === Chat Capability Models ===

class EmotionalContext(BaseModel):
    """Emotional context for chat interactions"""
    tone: Optional[str] = None  # detected emotional tone
    support_needed: bool = False  # user needs emotional support
    stress_level: Optional[Literal["low", "medium", "high"]] = None
    confidence_level: Optional[Literal["low", "medium", "high"]] = None


class UserContext(BaseModel):
    """User context for personalized responses"""
    industry: Optional[str] = "theater"  # theater, broadway, touring, music venue
    role: Optional[str] = None  # e.g., "marketing director", "box office manager"
    organization: Optional[str] = None  # e.g., "Shubert Organization"
    preferences: Dict[str, Any] = Field(default_factory=dict)


class ChatInputs(CapabilityInputs):
    """Chat-specific inputs"""
    message: str
    emotional_context: EmotionalContext
    conversation_history: List[Message] = Field(default_factory=list)
    user_context: Optional[UserContext] = None


class ChatResult(CapabilityResult):
    """Chat capability output"""
    response: str
    follow_up_questions: List[str] = Field(default_factory=list)
    emotional_tone: Optional[str] = None
    support_provided: bool = False


# === Ticketing Data Capability Models ===

class CubeFilter(BaseModel):
    """Single filter for Cube.js query"""
    member: str  # e.g., "productions.name"
    operator: str  # e.g., "equals", "contains", "in"
    values: List[str]


class TicketingDataInputs(CapabilityInputs):
    """Flexible data access - LLM decides query structure"""
    query_request: Optional[str] = None  # Natural language description
    time_context: Optional[str] = None  # e.g., "Q1 2023 vs Q2 2023"
    time_comparison_type: Optional[str] = None  # e.g., "year_over_year"
    measures: List[str]  # e.g., ["ticket_line_items.amount", "ticket_line_items.quantity"]
    dimensions: List[str] = Field(default_factory=list)  # e.g., ["productions.name", "time.month"]
    filters: List[CubeFilter] = Field(default_factory=list)
    order: Optional[Dict[str, str]] = None  # e.g., {"ticket_line_items.amount": "desc"}
    limit: Optional[int] = None
    entities: Optional[List[Dict[str, Any]]] = None  # Resolved entities from orchestrator


class DataPoint(BaseModel):
    """Single data point from query result"""
    dimensions: Dict[str, Any] = Field(default_factory=dict)
    measures: Dict[str, Any] = Field(default_factory=dict)


class TicketingDataResult(CapabilityResult):
    """Ticketing data capability output"""
    data: List[DataPoint]
    query_metadata: Dict[str, Any] = Field(default_factory=dict)
    total_rows: int = 0
    total_columns: int = 0
    total_measures: int = 0
    assumptions: List[str] = Field(default_factory=list)  # What was assumed during query


# === Event Analysis Capability Models ===

class AnalysisCriteria(BaseModel):
    """Flexible analysis criteria from LLM"""
    analysis_type: str  # e.g., "performance", "trends", "comparison"
    criteria: Dict[str, Any]  # LLM-defined criteria (no hardcoded thresholds)
    context: Dict[str, Any] = Field(default_factory=dict)  # Additional context


class EventAnalysisInputs(CapabilityInputs):
    """Event analysis inputs - MVP version"""
    analysis_request: str  # Natural language description of what to analyze
    data: Optional[Any] = None  # Data from TicketingDataCapability (optional)
    entities: List[Dict[str, Any]] = Field(default_factory=list)  # Resolved entities with IDs
    time_context: Optional[str] = None  # Time period for analysis


class AnalysisInsight(BaseModel):
    """Single insight from analysis"""
    type: str  # e.g., "trend", "anomaly", "comparison"
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_data: Dict[str, Any] = Field(default_factory=dict)


class EventAnalysisResult(CapabilityResult):
    """Event analysis capability output - MVP version"""
    insights: List[str] = Field(default_factory=list)  # Simple string insights for MVP
    recommendations: List[str] = Field(default_factory=list)
    analysis_complete: bool = False  # Whether analysis is done or needs more data
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    orchestrator_hints: Dict[str, Any] = Field(default_factory=dict)  # Hints for orchestrator


# === Memory Capability Models ===

class MemorySearchInputs(CapabilityInputs):
    """Memory search inputs"""
    query: str
    search_type: Literal["semantic", "conversation", "preference"] = "semantic"
    limit: int = 5


class MemoryItem(BaseModel):
    """Single memory item"""
    id: str
    content: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemorySearchResult(CapabilityResult):
    """Memory search capability output"""
    items: List[MemoryItem]
    total_found: int = 0


class MemoryStoreInputs(CapabilityInputs):
    """Memory storage inputs"""
    content: str
    memory_type: Literal["conversation", "preference", "insight"] = "conversation"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryStoreResult(CapabilityResult):
    """Memory storage capability output"""
    memory_id: str
    stored: bool = True