"""
Refactored orchestrate_node showing how to fix the symptom patches
This is a proposal - not to replace the current file yet
"""

from typing import Optional, Dict, Any
from models.state import AgentState, TaskResult
from models.orchestration import FinalResponse

class ResponseGenerator:
    """Generate appropriate responses from completed tasks"""
    
    @staticmethod
    def generate_from_tasks(state: AgentState, orchestrator_response: Optional[str] = None) -> FinalResponse:
        """Generate final response from completed tasks"""
        
        # If orchestrator provided a specific response, use it
        if orchestrator_response:
            return FinalResponse(
                message=orchestrator_response,
                confidence=0.9
            )
        
        # Otherwise, generate from task results
        if not state.execution.completed_tasks:
            return FinalResponse(
                message="Task completed successfully",
                confidence=0.8
            )
        
        # Get most recent task
        recent_task = list(state.execution.completed_tasks.values())[-1]
        
        # Generate response based on capability type
        if recent_task.capability == "ticketing_data":
            return ResponseGenerator._generate_data_response(recent_task, state)
        elif recent_task.capability == "event_analysis":
            return ResponseGenerator._generate_analysis_response(recent_task, state)
        elif recent_task.capability == "chat":
            return ResponseGenerator._generate_chat_response(recent_task, state)
        else:
            return FinalResponse(
                message="Analysis completed",
                data_source=recent_task.task_id,
                confidence=0.8
            )
    
    @staticmethod
    def _generate_data_response(task: TaskResult, state: AgentState) -> FinalResponse:
        """Generate response for data retrieval tasks"""
        if not task.success:
            return FinalResponse(
                message="Unable to retrieve the requested data",
                confidence=0.5
            )
        
        # Extract data value
        data = task.result.get("data", [])
        if not data or not isinstance(data[0], dict):
            return FinalResponse(
                message="Data retrieved but no values found",
                confidence=0.7
            )
        
        # Get measure value
        measures = data[0].get("measures", {})
        if not measures:
            return FinalResponse(
                message="Query completed but no metrics found",
                confidence=0.7
            )
        
        # Get the value and format response
        value = list(measures.values())[0]
        measure_name = list(measures.keys())[0]
        
        # Get entity name from state
        entity_name = ResponseGenerator._extract_entity_name(state)
        
        # Format based on measure type
        if "amount" in measure_name or "revenue" in measure_name:
            message = f"The total revenue for {entity_name} is ${value:,.2f}"
        elif "quantity" in measure_name or "count" in measure_name:
            message = f"The total tickets sold for {entity_name} is {value:,.0f}"
        else:
            message = f"The {measure_name} for {entity_name} is {value:,.2f}"
        
        return FinalResponse(
            message=message,
            data_source=task.task_id,
            confidence=0.95
        )
    
    @staticmethod
    def _extract_entity_name(state: AgentState) -> str:
        """Extract primary entity name from state"""
        if state.semantic.frames:
            frame = state.semantic.frames[0]
            # Look for production entity first
            for entity in frame.entities:
                if entity.type == "production":
                    return entity.text
            # Fall back to any entity
            if frame.entities:
                return frame.entities[0].text
        return "the requested entity"
    
    @staticmethod
    def _generate_analysis_response(task: TaskResult, state: AgentState) -> FinalResponse:
        """Generate response for analysis tasks"""
        # Implementation for analysis responses
        pass
    
    @staticmethod  
    def _generate_chat_response(task: TaskResult, state: AgentState) -> FinalResponse:
        """Generate response for chat tasks"""
        # Implementation for chat responses
        pass


class OrchestrationConstants:
    """Constants for orchestration configuration"""
    ENTITY_CONFIDENCE_THRESHOLD = 0.5
    CONVERSATION_CONTEXT_SIZE = 6
    MAX_ORCHESTRATION_LOOPS = 10
    ORCHESTRATOR_TEMPERATURE = 0.3
    DEFAULT_FRAME_ID = "0"


class RefactoredOrchestrationNode:
    """Example of how to refactor the orchestrate_node"""
    
    async def orchestrate_node(self, state: AgentState) -> AgentState:
        """Main orchestration - decide next single task"""
        
        logger.info(f"=== Orchestration loop {state.execution.loop_count} ===")
        logger.info(f"Query: {state.core.query}")
        logger.info(f"Completed tasks: {list(state.execution.completed_tasks.keys())}")
        
        # Check loop limit
        if state.execution.loop_count >= OrchestrationConstants.MAX_ORCHESTRATION_LOOPS:
            state.core.status = "error"
            state.add_message("system", "Maximum execution loops exceeded")
            state.routing.next_node = "end"
            return state
        
        # Build orchestration context
        context = self._build_orchestration_context(state)
        
        # Get orchestration decision
        decision = await self._get_orchestration_decision(context)
        logger.info(f"Decision: {decision.action} - {getattr(decision, 'capability', 'N/A')}")
        
        # Handle decision
        if decision.action == "complete":
            # Use ResponseGenerator instead of inline logic
            state.core.final_response = ResponseGenerator.generate_from_tasks(
                state, 
                orchestrator_response=decision.response
            )
            state.core.status = "complete"
            state.routing.next_node = "end"
        else:
            # Execute capability
            self._prepare_task_execution(state, decision)
            state.routing.next_node = "execute_capability"
            state.routing.capability_to_execute = decision.capability
        
        # Increment loop counter
        state.increment_loop()
        
        return state
    
    def _prepare_task_execution(self, state: AgentState, decision: OrchestrationDecision) -> None:
        """Prepare state for task execution"""
        task_id = f"t{len(state.execution.completed_tasks)+1}"
        
        # Create Task model
        current_task = Task(
            id=task_id,
            capability=decision.capability,
            inputs=decision.inputs or {}
        )
        
        # Store in state properly instead of message metadata
        state.execution.current_task = current_task  # This would require adding to ExecutionState
        
        # Still add message for audit trail
        state.add_message(
            "system", 
            f"Executing task {task_id}: {decision.capability}"
        )