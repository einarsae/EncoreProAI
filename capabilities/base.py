"""
Base Capability Interface

Defines the interface that all capabilities must implement.
Each capability is self-contained and handles its own business logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, TYPE_CHECKING, Optional
from pydantic import BaseModel

from models.capabilities import CapabilityInputs, CapabilityResult

if TYPE_CHECKING:
    from models.state import AgentState


class ResponseContext(BaseModel):
    """Context for formatting responses"""
    entity_name: Optional[str] = None
    query: str
    task_id: str
    

class CapabilityDescription(BaseModel):
    """Description of a capability for LLM understanding"""
    name: str
    purpose: str
    category: str = "general"  # data, analysis, communication, planning, action
    inputs: Dict[str, Any]  # Field descriptions, not just strings
    outputs: Dict[str, Any]  # Output descriptions, not just strings
    examples: List[str]
    routing_hints: Optional[Dict[str, List[str]]] = None  # Keywords/concepts for routing


class BaseCapability(ABC):
    """Base interface for all capabilities"""
    
    @abstractmethod
    def describe(self) -> CapabilityDescription:
        """Describe capability for LLM orchestrator"""
        pass
    
    @abstractmethod
    async def execute(self, inputs: CapabilityInputs) -> CapabilityResult:
        """Execute capability with typed inputs/outputs"""
        pass
    
    def get_name(self) -> str:
        """Get capability name"""
        return self.describe().name
    
    def build_inputs(self, task: Dict[str, Any], state: "AgentState") -> CapabilityInputs:
        """
        Build capability inputs from task and state.
        Override this method in specific capabilities for custom logic.
        
        Args:
            task: Task dict with 'inputs' field containing orchestrator-provided inputs
            state: Current agent state with session info and context
            
        Returns:
            CapabilityInputs or subclass specific to this capability
        """
        # Default implementation - merge common fields with task inputs
        base_fields = {
            "session_id": state.core.session_id,
            "tenant_id": state.core.tenant_id,
            "user_id": state.core.user_id
        }
        
        # Merge with task inputs
        task_inputs = task.get("inputs", {})
        
        # Return generic CapabilityInputs - capabilities should override this
        return CapabilityInputs(**{**base_fields, **task_inputs})
    
    def summarize_result(self, result: CapabilityResult) -> str:
        """
        Summarize result for human consumption.
        Override this method for custom summaries.
        
        Args:
            result: The capability result to summarize
            
        Returns:
            Human-readable summary string
        """
        if hasattr(result, 'summary') and result.summary:
            return result.summary
        
        if hasattr(result, 'success'):
            status = "completed successfully" if result.success else "failed"
            return f"{self.get_name()} {status}"
        
        return f"{self.get_name()} completed"
    
    def prepare_response_context(self, result: CapabilityResult) -> Dict[str, Any]:
        """
        Prepare condensed context for LLM response generation.
        Override this method to provide capability-specific context.
        
        Args:
            result: The capability result to prepare context from
            
        Returns:
            Dictionary with key information for response generation
            without overwhelming the LLM with raw data
        """
        # Default implementation - just provide summary
        context = {
            "summary": self.summarize_result(result),
            "success": result.success if hasattr(result, 'success') else True,
        }
        
        # Add error info if present
        if hasattr(result, 'error_message') and result.error_message:
            context["error"] = result.error_message
            
        return context