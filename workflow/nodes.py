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
from services.entity_helpers import EntityHelpers
from services.response_generator import ResponseGenerator
from services.orchestration_context import OrchestrationContextBuilder
from capabilities.base import BaseCapability

logger = logging.getLogger(__name__)


class WorkflowNodes:
    """Container for all workflow nodes"""
    
    # Configuration constants
    ENTITY_CONFIDENCE_THRESHOLD = 0.5
    CONVERSATION_CONTEXT_SIZE = 6
    ORCHESTRATOR_TEMPERATURE = 0.3
    DEFAULT_FRAME_ID = "0"
    
    def __init__(self):
        # Initialize services
        self.frame_extractor = FrameExtractor()
        self.entity_resolver = EntityResolver(
            database_url=os.getenv("DATABASE_URL", "postgresql://encore:secure_password@postgres:5432/encoreproai")
        )
        
        # Initialize capabilities dynamically
        from capabilities.registry import get_registry
        registry = get_registry()
        self.capabilities = registry.get_all_instances()
        
        # Initialize context builder with capabilities
        self.context_builder = OrchestrationContextBuilder(self.capabilities)
        
        # Initialize response generator
        self.response_generator = ResponseGenerator()
        
        # Initialize LLM for orchestration
        if os.getenv("ANTHROPIC_API_KEY"):
            self.orchestrator_llm = ChatAnthropic(
                model=os.getenv("LLM_CHAT_STANDARD", "claude-sonnet-4-20250514"),
                temperature=self.ORCHESTRATOR_TEMPERATURE  # Lower for more consistent orchestration
            )
        else:
            self.orchestrator_llm = ChatOpenAI(
                model=os.getenv("LLM_TIER_STANDARD", "gpt-4o-mini"),
                temperature=self.ORCHESTRATOR_TEMPERATURE
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
            recent_messages = state.core.messages[-self.CONVERSATION_CONTEXT_SIZE:]  # Last 3 exchanges
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
            state.semantic.current_frame_id = self.DEFAULT_FRAME_ID  # Start with first frame
        
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
            if not candidates or (candidates and candidates[0].score < self.ENTITY_CONFIDENCE_THRESHOLD):
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
        
        logger.info(f"=== Orchestration loop {state.execution.loop_count} ===")
        logger.info(f"Query: {state.core.query}")
        logger.info(f"Completed tasks: {list(state.execution.completed_tasks.keys())}")
        
        # Check loop limit
        if state.has_loop_limit_exceeded():
            state.core.status = "error"
            state.add_message("system", "Maximum execution loops exceeded")
            state.routing.next_node = "end"
            return state
        
        # Build orchestration context
        context = self.context_builder.build_context(state)
        
        # Get orchestration decision
        decision = await self._get_orchestration_decision(context)
        logger.info(f"Decision: {decision.action} - {getattr(decision, 'capability', 'N/A')}")
        
        # Handle decision
        if decision.action == "complete":
            # Done - format final response
            logger.info(f"Completing with response type: {type(decision.response)}")
            logger.info(f"Response content: {decision.response}")
            
            # Generate final response using ResponseGenerator
            state.core.final_response = await self.response_generator.generate_response(
                state=state,
                orchestrator_response=decision.response
            )
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
    
    
    async def execute_capability_node(self, state: AgentState) -> AgentState:
        """Generic capability execution - works with any capability"""
        
        # Get capability to execute
        capability_name = state.routing.capability_to_execute
        logger.info(f"=== Executing capability: {capability_name} ===")
        
        if not capability_name or capability_name not in self.capabilities:
            state.add_message("system", f"Invalid capability: {capability_name}")
            state.routing.next_node = "orchestrate"
            return state
        
        # Get current task from last system message
        task = None
        for msg in reversed(state.core.messages):
            if msg.role == "system" and msg.metadata and "current_task" in msg.metadata:
                task = msg.metadata["current_task"]
                logger.info(f"Found task: {task['id']}")
                break
        
        if not task:
            logger.warning("No task found in messages!")
            logger.info(f"Last 3 messages: {[(m.role, m.content[:50], bool(m.metadata)) for m in state.core.messages[-3:]]}")
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
            logger.info(f"Task {task['id']} completed successfully: {summary}")
            
        except Exception as e:
            logger.error(f"Error executing {capability_name}: {str(e)}", exc_info=True)
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
    
    
    async def _get_orchestration_decision(self, context: str) -> OrchestrationDecision:
        """Get orchestration decision from LLM"""
        
        messages = [
            SystemMessage(content="""You are an intelligent orchestrator for a theater analytics AI assistant.

Key principles:
1. Execute ONE task at a time - see results before next decision
2. Use semantic frame understanding (entities, concepts) to guide decisions
3. Read each capability's purpose and description to understand what it can do
4. Match user intent to the most appropriate capability based on its description

When ambiguous entities exist, you can:
- Select the most likely candidate based on context
- Select multiple candidates if all are relevant
- Ask for clarification if truly ambiguous

Decision making:
- Carefully read the purpose of each available capability
- Consider the user's query and the concepts/entities extracted
- Choose the capability that best matches the user's intent
- Let capabilities that need other data request it themselves

Input format notes:
- For data queries, use the format shown in the capability's input descriptions
- filters must be a list: [{"member": "field", "operator": "equals", "values": ["value"]}]
- measures and dimensions must be lists: ["field1", "field2"]
- When filtering by resolved entities, use the ID from "Resolved Entities" section
- For production filters, use {"member": "productions.id", "operator": "equals", "values": ["ID_FROM_RESOLVED_ENTITIES"]}

Remember: Each capability describes what it does. Use those descriptions to make routing decisions."""),
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
    
    
