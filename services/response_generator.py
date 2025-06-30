"""
Response generation service for creating final responses from task results

This service handles the conversion of task execution results into
user-friendly final responses using LLM-based generation with
condensed context from capabilities.
"""

from typing import Optional, List, Dict, Any, Union
import logging
import json
import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage
from models.state import AgentState, TaskResult
from models.orchestration import FinalResponse
from services.entity_helpers import EntityHelpers

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Generate final responses from completed tasks and orchestrator decisions"""
    
    # Confidence levels
    HIGH_CONFIDENCE = 0.95
    MEDIUM_CONFIDENCE = 0.9
    DEFAULT_CONFIDENCE = 0.8
    LOW_CONFIDENCE = 0.5
    
    def __init__(self):
        """Initialize with LLM for response generation"""
        # Initialize LLM for response generation
        if os.getenv("ANTHROPIC_API_KEY"):
            self.llm = ChatAnthropic(
                model=os.getenv("LLM_CHAT_FAST", "claude-3-5-haiku-20241022"),
                temperature=0.7
            )
        else:
            self.llm = ChatOpenAI(
                model=os.getenv("LLM_TIER_FAST", "gpt-4o-mini"),
                temperature=0.7
            )
    
    async def generate_response(
        self,
        state: AgentState, 
        orchestrator_response: Optional[Union[Dict[str, Any], str]] = None
    ) -> FinalResponse:
        """
        Generate final response from orchestrator decision and completed tasks
        
        Args:
            state: Current agent state with completed tasks
            orchestrator_response: Response from orchestrator (dict, str, or None)
            
        Returns:
            FinalResponse object ready to send to user
            
        Example:
            >>> response = await ResponseGenerator().generate_response(
            ...     state=agent_state,
            ...     orchestrator_response={"message": "Analysis complete"}
            ... )
        """
        # Validate input
        if not isinstance(state, AgentState):
            logger.error(f"Invalid state type: {type(state)}")
            return FinalResponse(
                message="An error occurred processing the response",
                confidence=ResponseGenerator.LOW_CONFIDENCE
            )
        
        # If we have completed tasks, generate response using capability context
        if state.execution.completed_tasks:
            return await self._generate_llm_response(state, orchestrator_response)
        
        # No tasks completed - use orchestrator response or default
        if isinstance(orchestrator_response, str):
            return FinalResponse(
                message=orchestrator_response,
                confidence=ResponseGenerator.MEDIUM_CONFIDENCE
            )
        elif isinstance(orchestrator_response, dict):
            return FinalResponse(
                message=orchestrator_response.get("message", "Task completed"),
                data_source=orchestrator_response.get("data_source"),
                insights=orchestrator_response.get("insights", []),
                recommendations=orchestrator_response.get("recommendations", [])
            )
        else:
            return FinalResponse(
                message="I've completed the task.",
                confidence=ResponseGenerator.DEFAULT_CONFIDENCE
            )
    
    async def _generate_llm_response(
        self, 
        state: AgentState,
        orchestrator_hint: Optional[Union[Dict[str, Any], str]] = None
    ) -> FinalResponse:
        """Generate response using LLM with capability context"""
        # Get the most recent task
        recent_task = list(state.execution.completed_tasks.values())[-1]
        
        # Get capability instance from registry
        from capabilities.registry import get_registry
        registry = get_registry()
        capability = registry.get_instance(recent_task.capability)
        
        if not capability:
            # Fallback if capability not found
            return FinalResponse(
                message=f"Completed {recent_task.capability} task.",
                confidence=ResponseGenerator.LOW_CONFIDENCE
            )
        
        # Get condensed context from capability
        try:
            # Most capabilities store their result as a dict in TaskResult.result
            # We need to pass this dict to prepare_response_context
            # The capability knows how to handle its own result format
            result = recent_task.result
            
            # Create a simple wrapper that has the attributes needed
            class ResultWrapper:
                def __init__(self, data):
                    self.__dict__.update(data)
                    # Ensure we have a success attribute
                    if 'success' not in data:
                        self.success = recent_task.success
            
            if isinstance(result, dict):
                result_obj = ResultWrapper(result)
                context = capability.prepare_response_context(result_obj)
            else:
                context = capability.prepare_response_context(result)
        except Exception as e:
            logger.error(f"Error preparing context: {e}")
            # Fallback to basic context
            context = {
                "summary": f"Completed {recent_task.capability} task",
                "success": recent_task.success,
                "error": str(e) if not recent_task.success else None
            }
        
        # Build prompt for LLM
        entity_name = self._get_entity_name(state)
        prompt = self._build_response_prompt(
            query=state.core.query,
            entity_name=entity_name,
            capability_name=recent_task.capability,
            context=context,
            orchestrator_hint=orchestrator_hint
        )
        
        # Generate response
        try:
            messages = [
                SystemMessage(content="""You are a helpful AI assistant providing clear, natural responses about theater data and analytics.

Guidelines:
- Be specific and precise with numbers and data
- If data includes currency, format it properly (e.g., $1,234.56)
- If data includes counts, use appropriate formatting (e.g., 1,234 tickets)
- For multiple records, summarize key findings
- Maintain a professional yet friendly tone
- If there were errors or no data, explain clearly
- Don't make up data - only report what's in the context"""),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            message = response.content
            
            return FinalResponse(
                message=message,
                data_source=recent_task.task_id,
                confidence=ResponseGenerator.HIGH_CONFIDENCE if recent_task.success else ResponseGenerator.MEDIUM_CONFIDENCE
            )
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # Fallback to basic response
            return FinalResponse(
                message=context.get("summary", "Task completed."),
                data_source=recent_task.task_id,
                confidence=ResponseGenerator.LOW_CONFIDENCE
            )
    
    def _build_response_prompt(
        self,
        query: str,
        entity_name: str,
        capability_name: str,
        context: Dict[str, Any],
        orchestrator_hint: Optional[Any] = None
    ) -> str:
        """Build prompt for response generation"""
        prompt_parts = [
            f"User Query: {query}",
            f"Primary Entity: {entity_name}",
            f"\nTask Type: {capability_name}",
            f"\nResult Context:\n{json.dumps(context, indent=2)}"
        ]
        
        if orchestrator_hint:
            if isinstance(orchestrator_hint, str):
                prompt_parts.append(f"\nResponse Guidance: {orchestrator_hint}")
            elif isinstance(orchestrator_hint, dict) and "message" in orchestrator_hint:
                prompt_parts.append(f"\nResponse Guidance: {orchestrator_hint['message']}")
        
        prompt_parts.append("\nGenerate a helpful, natural response based on this context.")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def _get_entity_name(state: AgentState) -> str:
        """Get primary entity name from state"""
        if not state.semantic.frames or not state.semantic.frames[0].resolved_entities:
            return "the requested entity"
        
        frame = state.semantic.frames[0]
        
        # Look for production entity first
        resolved = EntityHelpers.get_best_by_type(frame.resolved_entities, "production")
        if resolved:
            return EntityHelpers.get_display_name(resolved)
        
        # Fall back to first high-confidence entity
        for resolved in frame.resolved_entities:
            if EntityHelpers.is_high_confidence(resolved):
                return EntityHelpers.get_display_name(resolved)
        
        # Last resort: first entity text
        if frame.entities:
            return frame.entities[0].text
        
        return "the requested entity"