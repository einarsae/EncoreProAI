"""
LangGraph Workflow Nodes

Each node is a step in the orchestration process.
Nodes operate on AgentState and return updated state.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from models.state import AgentState, TaskResult, ExecutionState
from models.frame import Frame, EntityToResolve
from models.orchestration import Task, OrchestrationDecision, FinalResponse
from services.frame_extractor import FrameExtractor
from services.entity_resolver import EntityResolver
from services.concept_resolver import ConceptResolver
from capabilities.base import BaseCapability
from capabilities.chat import ChatCapability
from capabilities.ticketing_data import TicketingDataCapability
from capabilities.event_analysis import EventAnalysisCapability
from models.capabilities import (
    ChatInputs, EmotionalContext, UserContext,
    TicketingDataInputs, CubeFilter,
    EventAnalysisInputs
)

logger = logging.getLogger(__name__)


class WorkflowNodes:
    """Container for all workflow nodes"""
    
    def __init__(self):
        # Initialize services
        self.frame_extractor = FrameExtractor()
        self.entity_resolver = EntityResolver(
            database_url="postgresql://encore:secure_password@postgres:5432/encoreproai"
        )
        self.concept_resolver = ConceptResolver()
        
        # Initialize capabilities dynamically
        from capabilities.registry import get_registry
        registry = get_registry()
        self.capabilities = registry.get_all_instances()
        
        # Initialize LLM for orchestration
        if os.getenv("ANTHROPIC_API_KEY"):
            self.orchestrator_llm = ChatAnthropic(
                model=os.getenv("LLM_CHAT_STANDARD", "claude-sonnet-4-20250514"),
                temperature=0.3  # Lower for more consistent orchestration
            )
        else:
            self.orchestrator_llm = ChatOpenAI(
                model=os.getenv("LLM_TIER_STANDARD", "gpt-4o-mini"),
                temperature=0.3
            )
    
    async def extract_frames_node(self, state: AgentState) -> AgentState:
        """Extract semantic frames from user query"""
        
        # Build context for multi-turn conversations
        context = {
            "session_id": state.core.session_id,
            "previous_entities": []  # TODO: Extract from previous frames
        }
        
        # For multi-turn, include recent conversation context
        if state.core.messages:
            # Get last few exchanges for context
            recent_messages = state.core.messages[-6:]  # Last 3 exchanges
            context["conversation_history"] = [
                {"role": msg.role, "content": msg.content}
                for msg in recent_messages
            ]
        
        # Extract frames
        frames = await self.frame_extractor.extract_frames(
            state.core.query,
            context=context
        )
        
        # Update state
        state.semantic.frames = frames
        if frames:
            state.semantic.current_frame_id = "0"  # Start with first frame
        
        # Add trace
        if state.debug:
            state.debug.add_trace_event("frames_extracted", {
                "count": len(frames),
                "frames": [f.model_dump() for f in frames]
            })
        
        # Route to resolution or orchestrate
        # Note: This only resolves current frame, not all frames at once
        state.routing.next_node = "resolve_entities" if frames else "orchestrate"
        
        return state
    
    async def resolve_entities_node(self, state: AgentState) -> AgentState:
        """Resolve entities in current frame"""
        
        frame = state.get_current_frame()
        if not frame:
            state.routing.next_node = "orchestrate"
            return state
        
        # Resolve each entity
        for entity in frame.entities:
            # First try with the LLM-guessed type
            candidates = await self.entity_resolver.resolve_entity(
                text=entity.text,
                entity_type=entity.type,
                tenant_id=state.core.tenant_id
            )
            
            # If no good matches, try cross-type lookup
            if not candidates or (candidates and candidates[0].score < 0.5):
                cross_candidates = await self.entity_resolver.cross_type_lookup(
                    text=entity.text,
                    tenant_id=state.core.tenant_id
                )
                # Use cross-type results if better
                if cross_candidates and (not candidates or cross_candidates[0].score > candidates[0].score):
                    candidates = cross_candidates
            
            # Add to resolved entities
            from models.frame import ResolvedEntity
            
            resolved = ResolvedEntity(
                id=entity.id,
                text=entity.text,
                type=entity.type,
                candidates=candidates  # Already Pydantic models
            )
            frame.resolved_entities.append(resolved)
        
        # Route directly to orchestration (concepts resolved on-demand)
        state.routing.next_node = "orchestrate"
        
        return state
    
    async def orchestrate_node(self, state: AgentState) -> AgentState:
        """Main orchestration - decide next single task"""
        
        # Check loop limit
        if state.has_loop_limit_exceeded():
            state.core.status = "error"
            state.add_message("system", "Maximum execution loops exceeded")
            state.routing.next_node = "end"
            return state
        
        # Build orchestration context
        context = self._build_orchestration_context(state)
        
        # Get orchestration decision
        decision = await self._get_orchestration_decision(context)
        
        # Handle decision
        if decision.action == "complete":
            # Done - format final response
            if isinstance(decision.response, dict):
                # Convert dict to FinalResponse
                state.core.final_response = FinalResponse(
                    message=decision.response.get("message", "Task completed"),
                    data_source=decision.response.get("data_source"),
                    insights=decision.response.get("insights", []),
                    recommendations=decision.response.get("recommendations", [])
                )
            else:
                state.core.final_response = decision.response
            state.core.status = "complete"
            state.routing.next_node = "end"
        else:
            # Execute capability
            capability_name = decision.capability
            task_inputs = decision.inputs or {}
            
            # Create task with proper ID
            task_id = f"t{len(state.execution.completed_tasks)+1}"
            
            # Create Task model
            current_task = Task(
                id=task_id,
                capability=capability_name,
                inputs=task_inputs
            )
            
            # Add to state metadata for the execution node
            state.add_message("system", f"Executing task {task_id}: {capability_name}", 
                            metadata={"current_task": current_task.model_dump()})
            
            # Route to generic capability execution
            state.routing.next_node = "execute_capability"
            state.routing.capability_to_execute = capability_name
        
        # Increment loop counter
        state.increment_loop()
        
        return state
    
    async def execute_chat_node(self, state: AgentState) -> AgentState:
        """Execute chat capability"""
        
        # Get current task from last system message
        task = None
        for msg in reversed(state.core.messages):
            if msg.role == "system" and "current_task" in msg.metadata:
                task = msg.metadata["current_task"]
                break
        
        if not task:
            state.routing.next_node = "orchestrate"
            return state
        
        capability = self.capabilities["chat"]
        
        # Build chat inputs
        frame = state.get_current_frame()
        
        # Detect emotional context from frame
        emotional_context = self._detect_emotional_context(frame)
        
        # Get conversation history from state messages
        history = [msg for msg in state.core.messages if msg.role in ["user", "assistant"]]
        
        # Create inputs
        inputs = ChatInputs(
            session_id=state.core.session_id,
            tenant_id=state.core.tenant_id,
            user_id=state.core.user_id,
            message=state.core.query,
            emotional_context=emotional_context,
            conversation_history=history,
            user_context=UserContext()  # TODO: Get from user profile
        )
        
        # Execute
        try:
            result = await capability.execute(inputs)
            
            # Store result
            task_result = TaskResult(
                task_id=task["id"],
                capability="chat",
                inputs=task["inputs"],
                result=result.model_dump(),
                success=True
            )
            state.execution.add_task_result(task_result)
            
            # Add assistant message
            state.add_message("assistant", result.response)
            
        except Exception as e:
            task_result = TaskResult(
                task_id=task["id"],
                capability="chat",
                inputs=task["inputs"],
                result={},
                success=False,
                error_message=str(e)
            )
            state.execution.add_task_result(task_result)
        
        # Route back to orchestrate
        state.routing.next_node = "orchestrate"
        
        return state
    
    async def execute_ticketing_data_node(self, state: AgentState) -> AgentState:
        """Execute ticketing data capability"""
        
        # Get current task from last system message
        task = None
        for msg in reversed(state.core.messages):
            if msg.role == "system" and "current_task" in msg.metadata:
                task = msg.metadata["current_task"]
                break
        
        if not task:
            state.routing.next_node = "orchestrate"
            return state
        
        capability = self.capabilities["ticketing_data"]
        
        # Get inputs from task
        task_inputs = task.get("inputs", {})
        
        # Build ticketing data inputs from task
        # The orchestrator should provide these fields
        inputs = TicketingDataInputs(
            session_id=state.core.session_id,
            tenant_id=state.core.tenant_id,
            user_id=state.core.user_id,
            measures=task_inputs.get("measures", []),
            dimensions=task_inputs.get("dimensions", []),
            filters=[
                CubeFilter(**f) for f in task_inputs.get("filters", []) 
                if isinstance(f, dict) and f.get("member") and f.get("operator") and f.get("values")
            ],
            order=task_inputs.get("order"),
            limit=task_inputs.get("limit")
        )
        
        # Execute
        try:
            result = await capability.execute(inputs)
            
            # Store result
            task_result = TaskResult(
                task_id=task["id"],
                capability="ticketing_data",
                inputs=task["inputs"],
                result=result.model_dump(),
                success=result.success
            )
            state.execution.add_task_result(task_result)
            
            # Add system message with data summary
            if result.success and result.data:
                summary = f"Retrieved {len(result.data)} data points"
                state.add_message("system", f"Data fetched: {summary}")
            else:
                state.add_message("system", "No data retrieved")
            
        except Exception as e:
            task_result = TaskResult(
                task_id=task["id"],
                capability="ticketing_data",
                inputs=task["inputs"],
                result={},
                success=False,
                error_message=str(e)
            )
            state.execution.add_task_result(task_result)
            state.add_message("system", f"Data fetch failed: {str(e)}")
        
        # Route back to orchestrate
        state.routing.next_node = "orchestrate"
        
        return state
    
    async def execute_event_analysis_node(self, state: AgentState) -> AgentState:
        """Execute event analysis capability"""
        
        # Get current task from last system message
        task = None
        for msg in reversed(state.core.messages):
            if msg.role == "system" and "current_task" in msg.metadata:
                task = msg.metadata["current_task"]
                break
        
        if not task:
            state.routing.next_node = "orchestrate"
            return state
        
        capability = self.capabilities["event_analysis"]
        
        # Get inputs from task
        task_inputs = task.get("inputs", {})
        
        # Build event analysis inputs from task - MVP version
        inputs = EventAnalysisInputs(
            session_id=state.core.session_id,
            tenant_id=state.core.tenant_id,
            user_id=state.core.user_id,
            analysis_request=task_inputs.get("analysis_request", "General analysis"),
            data=task_inputs.get("data"),  # Optional data from previous capability
            entities=task_inputs.get("entities", []),  # Resolved entities with IDs
            time_context=task_inputs.get("time_context")
        )
        
        # Execute
        try:
            result = await capability.execute(inputs)
            
            # Store result
            task_result = TaskResult(
                task_id=task["id"],
                capability="event_analysis",
                inputs=task["inputs"],
                result=result.model_dump(),
                success=result.success
            )
            state.execution.add_task_result(task_result)
            
            # Add analysis summary to messages
            if result.success and result.summary:
                state.add_message("system", f"Analysis complete: {result.summary}")
            else:
                state.add_message("system", "Analysis completed with limited insights")
            
        except Exception as e:
            task_result = TaskResult(
                task_id=task["id"],
                capability="event_analysis",
                inputs=task["inputs"],
                result={},
                success=False,
                error_message=str(e)
            )
            state.execution.add_task_result(task_result)
            state.add_message("system", f"Analysis failed: {str(e)}")
        
        # Route back to orchestrate
        state.routing.next_node = "orchestrate"
        
        return state
    
    async def execute_capability_node(self, state: AgentState) -> AgentState:
        """Generic capability execution - works with any capability"""
        
        # Get capability to execute
        capability_name = state.routing.capability_to_execute
        if not capability_name or capability_name not in self.capabilities:
            state.add_message("system", f"Invalid capability: {capability_name}")
            state.routing.next_node = "orchestrate"
            return state
        
        # Get current task from last system message
        task = None
        for msg in reversed(state.core.messages):
            if msg.role == "system" and "current_task" in msg.metadata:
                task = msg.metadata["current_task"]
                break
        
        if not task:
            state.routing.next_node = "orchestrate"
            return state
        
        capability = self.capabilities[capability_name]
        
        try:
            # Let capability build its own inputs
            inputs = capability.build_inputs(task, state)
            
            # Execute capability
            result = await capability.execute(inputs)
            
            # Store result
            task_result = TaskResult(
                task_id=task["id"],
                capability=capability_name,
                inputs=task["inputs"],
                result=result.model_dump() if hasattr(result, 'model_dump') else result,
                success=getattr(result, 'success', True)
            )
            state.execution.add_task_result(task_result)
            
            # Add summary to messages
            summary = capability.summarize_result(result)
            state.add_message("system", summary)
            
        except Exception as e:
            # Handle errors
            task_result = TaskResult(
                task_id=task["id"],
                capability=capability_name,
                inputs=task["inputs"],
                result={},
                success=False,
                error_message=str(e)
            )
            state.execution.add_task_result(task_result)
            state.add_message("system", f"{capability_name} execution failed: {str(e)}")
        
        # Always route back to orchestrate
        state.routing.next_node = "orchestrate"
        return state
    
    def _build_orchestration_context(self, state: AgentState) -> str:
        """Build context for orchestration decision"""
        
        frame = state.get_current_frame()
        
        # Frame understanding
        frame_context = ""
        if frame:
            entities = [f"{e.text} ({e.type})" for e in frame.entities]
            concepts = frame.concepts
            
            # Show resolved entities with IDs for filtering
            resolved_info = []
            ambiguous = []
            for resolved in frame.resolved_entities:
                if resolved.candidates:
                    # Show best candidate with ID
                    best = resolved.candidates[0]
                    resolved_info.append(f"{resolved.text} → {best.name} (ID: {best.id}, type: {best.entity_type})")
                    
                    # Track ambiguous ones
                    if len(resolved.candidates) > 1:
                        candidates_str = "\n".join([
                            f"  - {c.name} (ID: {c.id}, {c.entity_type}): {c.disambiguation}"
                            for c in resolved.candidates[:3]
                        ])
                        ambiguous.append(f"{resolved.text} could be:\n{candidates_str}")
            
            # Resolve concepts on-demand for context
            concept_insights = []
            for concept in concepts:
                memory_context = self.concept_resolver.resolve(concept, state.core.user_id)
                if memory_context.get("source") == "memory":
                    concept_insights.append(f"  - {concept}: Previously used for {memory_context.get('concept')} analysis")
                else:
                    concept_insights.append(f"  - {concept}: Maps to {memory_context.get('concept')}")
            
            frame_context = f"""
Semantic Understanding:
- Entities: {entities}
- Concepts: {concepts}
{("- Resolved Entities (with IDs for filtering):" + chr(10) + "  " + (chr(10) + "  ").join(resolved_info)) if resolved_info else ""}
{("- Concept Insights:" + chr(10) + chr(10).join(concept_insights)) if concept_insights else ""}
{("- Ambiguous Entities:" + chr(10) + chr(10).join(ambiguous)) if ambiguous else ""}
"""
        
        # Completed tasks
        completed_context = ""
        if state.execution.completed_tasks:
            task_summaries = []
            for tid, result in state.execution.completed_tasks.items():
                task_summaries.append(f"- {tid}: {result.capability} (success={result.success})")
            completed_context = f"\nCompleted Tasks:\n" + "\n".join(task_summaries)
        
        # Build capabilities context dynamically from loaded capabilities
        capabilities_context = self._build_capabilities_context()
        
        return f"""
User Query: {state.core.query}

{frame_context}
{completed_context}
{capabilities_context}

Based on the semantic understanding and completed tasks, what is the NEXT SINGLE task?

Before deciding, ask yourself:
- Do I have enough data to complete this analysis?
- Would additional data from a different angle help provide better insights?
- Can I answer the user's question with what I have, or do I need more information?

Options:
1. Execute a capability (specify which one and inputs)
2. Complete with final response

Respond with JSON:
{{
    "action": "execute" or "complete",
    "capability": "capability_name" (if execute),
    "inputs": {{...}} (if execute),
    "response": {{...}} (if complete)
}}
"""
    
    def _build_capabilities_context(self) -> str:
        """Build capabilities context dynamically from loaded capabilities"""
        
        capabilities_text = "\n\nAvailable Capabilities:"
        
        for name, capability in self.capabilities.items():
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
            
            # Add examples if provided
            if description.examples:
                capabilities_text += "\n  Examples:"
                for example in description.examples:
                    capabilities_text += f"\n    - {example}"
        
        return capabilities_text
    
    async def _get_orchestration_decision(self, context: str) -> OrchestrationDecision:
        """Get orchestration decision from LLM"""
        
        messages = [
            SystemMessage(content="""You are an intelligent orchestrator for a theater analytics AI assistant.

Key principles:
1. Execute ONE task at a time - see results before next decision
2. Use semantic frame understanding (entities, concepts) to guide decisions
3. Route by intent:
   - Emotional support (overwhelmed, stressed, confused) → chat
   - Analysis requests (trends, patterns, compare, analyze, insights) → event_analysis
   - Data requests (show me, get, fetch, revenue for, attendance of) → ticketing_data
4. event_analysis will request data from ticketing_data if needed

When ambiguous entities exist, you can:
- Select the most likely candidate based on context
- Select multiple candidates if all are relevant
- Ask for clarification via chat if truly ambiguous"""),
            HumanMessage(content=context)
        ]
        
        response = await self.orchestrator_llm.ainvoke(messages)
        
        # Parse JSON response
        try:
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                decision_data = json.loads(json_match.group())
                return OrchestrationDecision(**decision_data)
        except Exception as e:
            logger.warning(f"Failed to parse orchestration decision: {e}")
        
        # Default to chat if parsing fails
        return OrchestrationDecision(
            action="execute",
            capability="chat",
            inputs={}
        )
    
    def _detect_emotional_context(self, frame: Optional[Frame]) -> EmotionalContext:
        """Detect emotional context from frame"""
        
        if not frame:
            return EmotionalContext()
        
        # Check concepts for emotional indicators
        emotional_concepts = ["overwhelmed", "stressed", "frustrated", "anxious", "worried"]
        positive_concepts = ["excited", "happy", "positive", "confident"]
        
        concepts_lower = [c.lower() for c in frame.concepts]
        
        has_negative = any(ec in concepts_lower for ec in emotional_concepts)
        has_positive = any(pc in concepts_lower for pc in positive_concepts)
        
        if has_negative:
            return EmotionalContext(
                tone="stressed",
                support_needed=True,
                stress_level="high"
            )
        elif has_positive:
            return EmotionalContext(
                tone="positive",
                support_needed=False,
                confidence_level="high"
            )
        else:
            return EmotionalContext(
                tone="neutral",
                support_needed=False
            )