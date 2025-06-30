"""
Workflow-specific models and enums

Constants and types used throughout the workflow orchestration.
"""

from enum import Enum


class NodeName(str, Enum):
    """Valid node names in the workflow graph"""
    EXTRACT_FRAMES = "extract_frames"
    RESOLVE_ENTITIES = "resolve_entities"
    ORCHESTRATE = "orchestrate"
    EXECUTE_CHAT = "execute_chat"
    EXECUTE_TICKETING_DATA = "execute_ticketing_data"
    EXECUTE_EVENT_ANALYSIS = "execute_event_analysis"
    END = "end"
    
    @classmethod
    def execution_node(cls, capability: str) -> str:
        """Generate execution node name for a capability"""
        return f"execute_{capability}"