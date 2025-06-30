"""
Help Capability - Explains what the system can do

This is a meta-capability that helps users understand available functionality.
"""

from typing import Dict, Any
from capabilities.base import BaseCapability, CapabilityDescription
from models.capabilities import CapabilityInputs, CapabilityResult
from capabilities.registry import get_registry


class HelpInputs(CapabilityInputs):
    """Inputs for help capability"""
    query: str = "What can you help me with?"
    category: str = None  # Optional: specific category to ask about


class HelpResult(CapabilityResult):
    """Result from help capability"""
    help_text: str
    available_capabilities: list
    suggested_queries: list = []


class HelpCapability(BaseCapability):
    """Capability that explains what the system can do"""
    
    def describe(self) -> CapabilityDescription:
        """Describe help capability"""
        return CapabilityDescription(
            name="help",
            purpose="Explain what I can do and guide you to the right capabilities",
            category="communication",
            inputs={
                "query": "What you want to know about (optional)",
                "category": "Specific category to explore (optional)"
            },
            outputs={
                "help_text": "Formatted explanation of capabilities",
                "available_capabilities": "List of available capabilities",
                "suggested_queries": "Example queries you can try"
            },
            examples=[
                "What can you help me with?",
                "What kind of analysis can you do?",
                "How can you help with data?",
                "Show me all capabilities"
            ]
        )
    
    def build_inputs(self, task: Dict[str, Any], state) -> HelpInputs:
        """Build inputs from task and state"""
        task_inputs = task.get("inputs", {})
        
        return HelpInputs(
            session_id=state.core.session_id,
            tenant_id=state.core.tenant_id,
            user_id=state.core.user_id,
            query=task_inputs.get("query", "What can you help me with?"),
            category=task_inputs.get("category")
        )
    
    async def execute(self, inputs: HelpInputs) -> HelpResult:
        """Generate help text dynamically from registry"""
        
        registry = get_registry()
        
        # Get help text
        help_text = registry.get_help_text()
        
        # Get capabilities summary
        capabilities = registry.get_capabilities_summary()
        
        # Generate suggested queries based on available capabilities
        suggested_queries = []
        for cap in capabilities:
            if cap["examples"]:
                suggested_queries.extend(cap["examples"][:1])  # One example per capability
        
        # If user asked about specific category, filter
        if inputs.category:
            help_text = f"Here's what I can help with in {inputs.category}:\n\n"
            capabilities = [c for c in capabilities if c["category"] == inputs.category]
            
            if capabilities:
                for cap in capabilities:
                    help_text += f"• {cap['purpose']}\n"
                    if cap['examples']:
                        help_text += f"  Example: \"{cap['examples'][0]}\"\n"
            else:
                help_text += f"I don't have any capabilities in the '{inputs.category}' category yet."
        
        return HelpResult(
            success=True,
            help_text=help_text,
            available_capabilities=capabilities,
            suggested_queries=suggested_queries[:5]  # Limit suggestions
        )
    
    def summarize_result(self, result: HelpResult) -> str:
        """Summarize help result"""
        return "Here's what I can help you with..."