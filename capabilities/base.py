"""
Base Capability Interface

Defines the interface that all capabilities must implement.
Each capability is self-contained and handles its own business logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from pydantic import BaseModel

from models.capabilities import CapabilityInputs, CapabilityResult


class CapabilityDescription(BaseModel):
    """Description of a capability for LLM understanding"""
    name: str
    purpose: str
    inputs: Dict[str, Any]  # Field descriptions, not just strings
    outputs: Dict[str, Any]  # Output descriptions, not just strings
    examples: List[str]


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