"""
Orchestration-specific models

These models define the data structures used in the orchestration workflow,
replacing dict usage with proper Pydantic validation.
"""

from typing import Dict, Any, Optional, Literal, List
from pydantic import BaseModel, Field
from datetime import datetime


class Task(BaseModel):
    """Represents a task to be executed by a capability"""
    id: str = Field(..., description="Task ID like t1, t2")
    capability: str = Field(..., description="Capability name to execute")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Inputs for the capability")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "t1",
                "capability": "ticketing_data",
                "inputs": {
                    "query_request": "Show revenue by month",
                    "measures": ["revenue"],
                    "dimensions": ["by month"]
                }
            }
        }


class OrchestrationDecision(BaseModel):
    """Decision made by the orchestrator LLM"""
    action: Literal["execute", "complete"] = Field(..., description="Action to take")
    capability: Optional[str] = Field(None, description="Capability to execute (if action=execute)")
    inputs: Optional[Dict[str, Any]] = Field(None, description="Inputs for capability (if action=execute)")
    response: Optional[str] = Field(None, description="Final response message to user (if action=complete)")
    reasoning: Optional[str] = Field(None, description="LLM's reasoning for this decision")
    
    def model_post_init(self, __context):
        """Validate that required fields are present based on action"""
        if self.action == "execute" and not self.capability:
            raise ValueError("capability is required when action is 'execute'")
        if self.action == "complete" and not self.response:
            self.response = {"message": "Task completed successfully"}


class FinalResponse(BaseModel):
    """Structured final response from orchestration"""
    message: str = Field(..., description="Human-readable summary")
    data_source: Optional[str] = Field(None, description="Reference to task that provided data")
    insights: List[str] = Field(default_factory=list, description="Key insights from analysis")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence in response")
    include_previous_results: bool = Field(default=False, description="Whether to include raw data from tasks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Revenue analysis for Chicago shows strong performance",
                "data_source": "t1_ticketing_data",
                "insights": [
                    "Revenue increased 15% month-over-month",
                    "Weekend shows drive 70% of revenue"
                ],
                "recommendations": [
                    "Consider adding more weekend performances",
                    "Explore dynamic pricing for high-demand shows"
                ],
                "confidence": 0.9
            }
        }


class NodeName(str):
    """String subclass for node names with validation"""
    
    VALID_NODES = {
        "extract_frames",
        "resolve_entities", 
        "orchestrate",
        "execute_chat",
        "execute_ticketing_data",
        "execute_event_analysis",
        "end"
    }
    
    def __new__(cls, value: str):
        if value not in cls.VALID_NODES:
            raise ValueError(f"Invalid node name: {value}. Must be one of {cls.VALID_NODES}")
        return str.__new__(cls, value)


class OrchestrationContext(BaseModel):
    """Context passed to orchestrator for decision making"""
    user_query: str
    semantic_understanding: Dict[str, Any] = Field(default_factory=dict)
    completed_tasks: List[Task] = Field(default_factory=list)
    available_capabilities: List[str] = Field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int = 10