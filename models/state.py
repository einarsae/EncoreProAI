"""
State models for LangGraph workflow - Grouped architecture
Each state group handles related functionality for clarity and maintainability
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime

from models.frame import Frame
from models.orchestration import FinalResponse


class Message(BaseModel):
    """Individual message in conversation"""
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    """Result from executing a single task"""
    task_id: str
    capability: str
    inputs: Dict[str, Any]
    result: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None


class CoreState(BaseModel):
    """Identity and processing status"""
    session_id: str
    user_id: str
    tenant_id: str
    query: str
    status: Literal["processing", "complete", "error"] = "processing"
    current_node: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    final_response: Optional[FinalResponse] = None


class SemanticState(BaseModel):
    """All semantic understanding - Frame-based"""
    frames: List[Frame] = Field(default_factory=list)
    current_frame_id: Optional[str] = None


class ExecutionState(BaseModel):
    """Task execution with single-task pattern"""
    completed_tasks: Dict[str, TaskResult] = Field(default_factory=dict)
    loop_count: int = 0  # Simple loop protection
    
    def add_task_result(self, task_result: TaskResult) -> None:
        """Add completed task result"""
        self.completed_tasks[task_result.task_id] = task_result
    
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result by ID"""
        return self.completed_tasks.get(task_id)
    
    def get_recent_results(self, limit: int = 3) -> List[TaskResult]:
        """Get most recent task results"""
        results = list(self.completed_tasks.values())
        results.sort(key=lambda x: x.timestamp, reverse=True)
        return results[:limit]


class RoutingState(BaseModel):
    """Next node decisions"""
    next_node: str = "orchestrate"  # Default entry point
    capability_to_execute: Optional[str] = None  # For generic capability execution


class MemoryState(BaseModel):
    """Memory and user context references"""
    conversation_history: List[str] = Field(default_factory=list)  # Recent conversation IDs
    user_preferences: Dict[str, Any] = Field(default_factory=dict)  # How user prefers analysis
    domain_knowledge: Dict[str, Any] = Field(default_factory=dict)  # Theater industry context
    
    def add_conversation(self, conversation_id: str) -> None:
        """Add conversation to history, keep last 10"""
        self.conversation_history.append(conversation_id)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]


class DebugState(BaseModel):
    """Optional debug information"""
    trace_enabled: bool = False
    trace_events: List[Dict[str, Any]] = Field(default_factory=list)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    
    def add_trace_event(self, event: str, data: Dict[str, Any]) -> None:
        """Add debug trace event"""
        if self.trace_enabled:
            self.trace_events.append({
                "timestamp": datetime.now().isoformat(),
                "event": event,
                "data": data
            })


class AgentState(BaseModel):
    """Main state - passed between nodes (Grouped state architecture)"""
    core: CoreState
    routing: RoutingState = Field(default_factory=RoutingState)
    semantic: SemanticState = Field(default_factory=SemanticState)
    execution: ExecutionState = Field(default_factory=ExecutionState)
    memory: MemoryState = Field(default_factory=MemoryState)
    debug: Optional[DebugState] = None
    
    def increment_loop(self) -> None:
        """Increment execution loop counter"""
        self.execution.loop_count += 1
    
    def get_current_frame(self) -> Optional[Frame]:
        """Get currently active frame"""
        if not self.semantic.current_frame_id:
            return None
        
        # current_frame_id is now an index
        try:
            idx = int(self.semantic.current_frame_id)
            if 0 <= idx < len(self.semantic.frames):
                return self.semantic.frames[idx]
        except (ValueError, IndexError):
            pass
        return None
    
    def add_message(self, role: Literal["user", "assistant", "system"], content: str, metadata: Dict[str, Any] = None) -> None:
        """Add message to conversation"""
        message = Message(
            id=f"msg_{len(self.core.messages)}",
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.core.messages.append(message)
    
    def is_complete(self) -> bool:
        """Check if processing is complete"""
        return self.core.status in ["complete", "error"]
    
    def has_loop_limit_exceeded(self) -> bool:
        """Check if loop limit exceeded"""
        return self.execution.loop_count > 20  # Increased temporarily for debugging