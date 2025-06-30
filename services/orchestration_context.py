"""
Orchestration context builder service

This service builds context for orchestration decisions by combining
frame understanding, completed tasks, and available capabilities into
a structured prompt for the orchestrator LLM.
"""

from typing import Dict, List, Optional, Any, Protocol
import logging
from models.state import AgentState
from models.frame import Frame, ResolvedEntity
from services.entity_helpers import EntityHelpers
from services.concept_resolver import ConceptResolver
from capabilities.base import BaseCapability, CapabilityDescription

logger = logging.getLogger(__name__)


class CapabilityProtocol(Protocol):
    """Protocol defining the interface for capabilities"""
    def describe(self) -> CapabilityDescription:
        """Return capability description"""
        ...


class OrchestrationContextBuilder:
    """Builds context for orchestration decisions"""
    
    # Instructions template
    INSTRUCTIONS_TEMPLATE = """
Based on the semantic understanding and completed tasks, what is the NEXT SINGLE task?

CRITICAL DECISION RULES:
1. If you have SPECIFIC DATA that answers the user's question → COMPLETE immediately
2. If completed tasks show actual numbers/values (e.g., "revenue data: $50,000") → COMPLETE with that answer
3. If you already retrieved the same data type multiple times → COMPLETE with available data
4. Only execute MORE tasks if you genuinely need DIFFERENT data

Before deciding, ask yourself:
- Do I have the specific data needed to answer the user's question?
- Have I already retrieved this type of data successfully?
- Am I repeating the same capability unnecessarily?

Options:
1. Execute a capability (specify which one and inputs) - ONLY if you need NEW/DIFFERENT data
2. Complete with final response - if you have the data to answer the question

Respond with JSON:
{
    "action": "execute" or "complete",
    "capability": "capability_name" (if execute),
    "inputs": {...} (if execute),
    "response": "Your final answer to the user" (if complete)
}

EXAMPLES OF WHEN TO COMPLETE:
- "What is total revenue for Gatsby?" + completed task shows "revenue data: $50,000" → COMPLETE
- "How many tickets sold?" + completed task shows "attendance data: 1,200 tickets" → COMPLETE
- Any question where you have the specific data/number requested → COMPLETE immediately"""
    
    def __init__(self, capabilities: Dict[str, BaseCapability]):
        """
        Initialize with capabilities registry
        
        Args:
            capabilities: Dictionary of capability name to instance
        """
        if not capabilities:
            logger.warning("No capabilities provided to context builder")
        self.capabilities = capabilities or {}
        self.concept_resolver = ConceptResolver()
    
    def build_context(self, state: AgentState) -> str:
        """
        Build complete orchestration context
        
        Args:
            state: Current agent state
            
        Returns:
            Formatted context string for orchestrator
            
        Example Output:
            User Query: What is the revenue for Chicago?
            
            Semantic Understanding:
            - Entities: [Chicago (production)]
            - Concepts: [revenue]
            - Resolved Entities (with IDs for filtering):
              Chicago → Chicago (ID: prod_chicago, type: production)
            
            Available Capabilities:
            ...
        """
        if not isinstance(state, AgentState):
            logger.error(f"Invalid state type: {type(state)}")
            return "Error: Invalid state provided"
        sections = [
            self._build_query_section(state),
            self._build_semantic_section(state),
            self._build_completed_tasks_section(state),
            self._build_capabilities_section(),
            self._build_instructions()
        ]
        
        return "\n".join(filter(None, sections))
    
    def _build_query_section(self, state: AgentState) -> str:
        """Build query section"""
        return f"User Query: {state.core.query}"
    
    def _build_semantic_section(self, state: AgentState) -> str:
        """Build semantic understanding section"""
        frame = state.get_current_frame()
        if not frame:
            return ""
        
        # Basic info
        entities = [f"{e.text} ({e.type})" for e in frame.entities]
        concepts = frame.concepts
        
        sections = [
            "\nSemantic Understanding:",
            f"- Entities: {entities}",
            f"- Concepts: {concepts}"
        ]
        
        # Resolved entities
        resolved_info = []
        ambiguous = []
        
        for resolved in frame.resolved_entities:
            if EntityHelpers.is_high_confidence(resolved):
                # Clear match - show simple resolution
                best = EntityHelpers.get_best_candidate(resolved)
                resolved_info.append(f"{resolved.text} → {best.name} (ID: {best.id}, type: {best.entity_type})")
            elif EntityHelpers.is_ambiguous(resolved):
                # Ambiguous - show all good candidates
                ambiguous.append(EntityHelpers.format_ambiguity_context(resolved))
            elif resolved.candidates:
                # Low confidence single match
                best = resolved.candidates[0]
                resolved_info.append(f"{resolved.text} → {best.name} (ID: {best.id}, score: {best.score:.2f})")
        
        if resolved_info:
            sections.append("- Resolved Entities (with IDs for filtering):")
            sections.extend([f"  {info}" for info in resolved_info])
        
        # Concept insights
        concept_insights = self._build_concept_insights(concepts, state.core.user_id)
        if concept_insights:
            sections.append("- Concept Insights:")
            sections.extend(concept_insights)
        
        # Ambiguous entities
        if ambiguous:
            sections.append("- Ambiguous Entities:")
            sections.extend(ambiguous)
        
        return "\n".join(sections)
    
    def _build_concept_insights(self, concepts: List[str], user_id: str) -> List[str]:
        """Build insights from concept resolution"""
        insights = []
        for concept in concepts:
            try:
                memory_context = self.concept_resolver.resolve(concept, user_id)
                if isinstance(memory_context, dict):
                    if memory_context.get("source") == "memory":
                        insights.append(f"  - {concept}: Previously used for {memory_context.get('concept', 'unknown')} analysis")
                    else:
                        insights.append(f"  - {concept}: Maps to {memory_context.get('concept', concept)}")
                else:
                    logger.warning(f"Unexpected concept resolution result for {concept}: {type(memory_context)}")
                    insights.append(f"  - {concept}: Standard concept")
            except Exception as e:
                logger.error(f"Error resolving concept {concept}: {e}")
                insights.append(f"  - {concept}: Standard concept")
        return insights
    
    def _build_completed_tasks_section(self, state: AgentState) -> str:
        """Build completed tasks section"""
        if not state.execution.completed_tasks:
            return ""
        
        task_summaries = []
        for tid, result in state.execution.completed_tasks.items():
            summary = f"- {tid}: {result.capability} (success={result.success})"
            
            # Add result summary if available and successful
            if result.success and result.result:
                # Get a meaningful summary of the result
                result_summary = self._summarize_task_result(result.result)
                if result_summary:
                    summary += f"\n  Result: {result_summary}"
            elif not result.success and hasattr(result, 'error_message') and result.error_message:
                summary += f"\n  Error: {result.error_message}"
                
            task_summaries.append(summary)
        
        return "\nCompleted Tasks:\n" + "\n".join(task_summaries)
    
    def _summarize_task_result(self, result: Any) -> str:
        """Summarize task result for orchestrator context"""
        if not result:
            return ""
            
        try:
            # Handle different result types
            if isinstance(result, dict):
                # Look for common result fields
                if "data" in result and result["data"]:
                    data = result["data"]
                    if isinstance(data, list) and len(data) > 0:
                        # Try to extract meaningful info from the first record
                        first_record = data[0]
                        if isinstance(first_record, dict):
                            # Check if it has measures structure (Cube.js format)
                            if "measures" in first_record and isinstance(first_record["measures"], dict):
                                measures = first_record["measures"]
                                # Look for revenue/amount fields in measures
                                if "ticket_line_items.amount" in measures:
                                    amount = measures["ticket_line_items.amount"]
                                    try:
                                        amount_num = float(amount)
                                        return f"Retrieved revenue data: ${amount_num:,.2f}"
                                    except (ValueError, TypeError):
                                        return f"Retrieved revenue data: {amount}"
                                elif "ticket_line_items.quantity" in measures:
                                    qty = measures["ticket_line_items.quantity"]
                                    try:
                                        qty_num = int(float(qty))
                                        return f"Retrieved attendance data: {qty_num:,} tickets"
                                    except (ValueError, TypeError):
                                        return f"Retrieved attendance data: {qty} tickets"
                                else:
                                    # Show which measures were retrieved
                                    measure_names = list(measures.keys())
                                    return f"Retrieved {len(data)} records with measures: {', '.join(measure_names)}"
                            # Check for direct fields (flat structure)
                            elif "ticket_line_items.amount" in first_record:
                                amount = first_record["ticket_line_items.amount"]
                                return f"Retrieved revenue data: ${amount:,}" if isinstance(amount, (int, float)) else f"Retrieved revenue data: {amount}"
                            elif "amount" in first_record:
                                amount = first_record["amount"]
                                return f"Retrieved revenue data: ${amount:,}" if isinstance(amount, (int, float)) else f"Retrieved revenue data: {amount}"
                            elif "ticket_line_items.quantity" in first_record:
                                qty = first_record["ticket_line_items.quantity"]
                                return f"Retrieved attendance data: {qty:,} tickets" if isinstance(qty, (int, float)) else f"Retrieved attendance data: {qty}"
                            else:
                                # Generic record description
                                fields = list(first_record.keys())[:3]
                                return f"Retrieved {len(data)} records with fields: {', '.join(fields)}"
                        else:
                            return f"Retrieved {len(data)} records of data"
                    elif isinstance(data, dict):
                        return f"Retrieved data with {len(data)} fields"
                    else:
                        return f"Retrieved data: {str(data)[:100]}..."
                elif "key_findings" in result:
                    findings = result["key_findings"]
                    if isinstance(findings, list) and len(findings) > 0:
                        return f"Key findings: {'; '.join(findings[:2])}..."
                    else:
                        return f"Key findings: {str(findings)[:100]}..."
                elif "query_description" in result:
                    return f"Query: {result['query_description']}"
                else:
                    # Generic dict result
                    return f"Retrieved result with {len(result)} fields: {', '.join(list(result.keys())[:3])}..."
            else:
                # Convert to string and truncate
                result_str = str(result)
                return result_str[:100] + "..." if len(result_str) > 100 else result_str
        except Exception as e:
            logger.warning(f"Error summarizing task result: {e}")
            return "Result available but could not summarize"
    
    def _build_capabilities_section(self) -> str:
        """Build capabilities context dynamically"""
        if not self.capabilities:
            return "\n\nNo capabilities available"
            
        capabilities_text = "\n\nAvailable Capabilities:"
        
        for name, capability in self.capabilities.items():
            try:
                # Get capability description using its describe() method
                description = capability.describe()
                
                # Format capability information
                capabilities_text += f"\n\n- {description.name}: {description.purpose}"
                
                # Add inputs if specified
                if description.inputs:
                    capabilities_text += "\n  Inputs:"
                    for field, desc in description.inputs.items():
                        capabilities_text += f"\n    * {field}: {desc}"
                
                # Add outputs if specified
                if description.outputs:
                    capabilities_text += "\n  Outputs:"
                    for field, desc in description.outputs.items():
                        capabilities_text += f"\n    * {field}: {desc}"
                
                # Add examples if provided (limit to 3 for brevity)
                if description.examples:
                    capabilities_text += "\n  Examples:"
                    for example in description.examples[:3]:
                        capabilities_text += f"\n    - {example}"
            except Exception as e:
                logger.error(f"Error describing capability {name}: {e}")
                capabilities_text += f"\n\n- {name}: [Error loading description]"
        
        return capabilities_text
    
    def _build_instructions(self) -> str:
        """Build instructions for orchestrator"""
        return OrchestrationContextBuilder.INSTRUCTIONS_TEMPLATE