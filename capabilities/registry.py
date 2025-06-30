"""
Dynamic Capability Registry

Discovers and registers capabilities at runtime without hardcoding.
Follows the principle of dynamic discovery from our learnings.
"""

import importlib
import inspect
import os
from typing import Dict, Type, Optional, List
from pathlib import Path

from capabilities.base import BaseCapability, CapabilityDescription
from capabilities.chat import ChatCapability
from capabilities.ticketing_data import TicketingDataCapability
from capabilities.event_analysis import EventAnalysisCapability
from capabilities.help import HelpCapability


class CapabilityRegistry:
    """Registry for dynamic capability discovery and management"""
    
    # Default capabilities - can be overridden or extended
    DEFAULT_CAPABILITIES = {
        "chat": ChatCapability,
        "ticketing_data": TicketingDataCapability,
        "event_analysis": EventAnalysisCapability,
        "help": HelpCapability
    }
    
    # Category descriptions for user help
    CATEGORY_DESCRIPTIONS = {
        "data": "Retrieve and fetch data from various sources",
        "analysis": "Analyze data to find patterns, trends, and insights",
        "communication": "Chat, get support, and have conversations",
        "planning": "Plan strategies and create action plans",
        "action": "Take actions like creating reports or sending alerts",
        "general": "General purpose capabilities"
    }
    
    def __init__(self, auto_discover: bool = True):
        self._capabilities: Dict[str, Type[BaseCapability]] = {}
        self._instances: Dict[str, BaseCapability] = {}
        
        # Register default capabilities
        for name, capability_class in self.DEFAULT_CAPABILITIES.items():
            self.register(name, capability_class)
        
        # Auto-discover capabilities if enabled
        if auto_discover:
            self.discover_capabilities()
    
    def register(self, name: str, capability_class: Type[BaseCapability]) -> None:
        """Register a capability class"""
        if not issubclass(capability_class, BaseCapability):
            raise ValueError(f"{capability_class} must inherit from BaseCapability")
        
        self._capabilities[name] = capability_class
    
    def get_instance(self, name: str) -> Optional[BaseCapability]:
        """Get or create a capability instance"""
        if name not in self._capabilities:
            return None
        
        # Create instance if not exists
        if name not in self._instances:
            self._instances[name] = self._capabilities[name]()
        
        return self._instances[name]
    
    def get_all_instances(self) -> Dict[str, BaseCapability]:
        """Get all capability instances"""
        # Ensure all registered capabilities have instances
        for name in self._capabilities:
            self.get_instance(name)
        
        return self._instances.copy()
    
    def get_capabilities_by_category(self) -> Dict[str, List[BaseCapability]]:
        """Get all capabilities grouped by category"""
        result = {}
        
        for name, capability in self.get_all_instances().items():
            description = capability.describe()
            category = description.category
            
            if category not in result:
                result[category] = []
            result[category].append(capability)
        
        return result
    
    def get_help_text(self) -> str:
        """Generate user-friendly help text about available capabilities"""
        help_text = "I can help you with:\n\n"
        
        # Group by category
        capabilities_by_category = self.get_capabilities_by_category()
        
        # Sort categories for consistent display
        for category in sorted(capabilities_by_category.keys()):
            if category in self.CATEGORY_DESCRIPTIONS:
                help_text += f"**{category.title()}** - {self.CATEGORY_DESCRIPTIONS[category]}\n"
                
                # List capabilities in this category
                for capability in capabilities_by_category[category]:
                    description = capability.describe()
                    help_text += f"  • {description.purpose}\n"
                    
                    # Add a few examples
                    if description.examples:
                        examples = ', '.join(f'"{ex}"' for ex in description.examples[:2])
                        help_text += f"    For example: {examples}\n"
                
                help_text += "\n"
        
        help_text += "Just ask me naturally about what you need!"
        return help_text
    
    def get_capabilities_summary(self) -> List[Dict[str, any]]:
        """Get structured summary of all capabilities"""
        summary = []
        
        for name, capability in self.get_all_instances().items():
            description = capability.describe()
            
            summary.append({
                "name": name,
                "category": description.category,
                "purpose": description.purpose,
                "examples": description.examples[:3] if description.examples else []
            })
        
        return summary
    
    def discover_capabilities(self) -> None:
        """Discover capabilities from the capabilities directory"""
        capabilities_dir = Path(__file__).parent
        
        for file_path in capabilities_dir.glob("*.py"):
            if file_path.name.startswith("_") or file_path.name in ["base.py", "registry.py"]:
                continue
            
            module_name = file_path.stem
            try:
                # Import the module
                module = importlib.import_module(f"capabilities.{module_name}")
                
                # Find all BaseCapability subclasses
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseCapability) and 
                        obj != BaseCapability and
                        not name.startswith("_")):
                        
                        # Generate a name from the class name
                        capability_name = self._class_name_to_capability_name(name)
                        
                        # Only register if not already registered
                        if capability_name not in self._capabilities:
                            self.register(capability_name, obj)
            
            except Exception as e:
                # Log but don't fail on discovery errors
                print(f"Failed to discover capabilities from {module_name}: {e}")
    
    def _class_name_to_capability_name(self, class_name: str) -> str:
        """Convert class name to capability name"""
        # Remove "Capability" suffix if present
        if class_name.endswith("Capability"):
            class_name = class_name[:-10]
        
        # Convert to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', class_name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        
        return name


# Global registry instance
_registry = None


def get_registry() -> CapabilityRegistry:
    """Get the global capability registry"""
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
    return _registry


def register_capability(name: str, capability_class: Type[BaseCapability]) -> None:
    """Register a capability with the global registry"""
    get_registry().register(name, capability_class)