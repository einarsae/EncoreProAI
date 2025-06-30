# WorkflowNodes Refactoring Plan

## Current Issues
- 796 lines in a single class
- Too many responsibilities
- Massive methods (orchestrate_node is ~100 lines)
- Code duplication
- Poor separation of concerns

## Proposed Structure

### 1. **WorkflowNodes** (workflow/nodes.py) - ~150 lines
```python
class WorkflowNodes:
    """Thin orchestration layer that delegates to specialized services"""
    
    def __init__(self):
        self.frame_service = FrameExtractionService()
        self.entity_service = EntityResolutionService()
        self.orchestration_service = OrchestrationService()
        self.capability_executor = CapabilityExecutor()
    
    async def extract_frames_node(self, state: AgentState) -> AgentState:
        return await self.frame_service.extract_frames(state)
    
    async def resolve_entities_node(self, state: AgentState) -> AgentState:
        return await self.entity_service.resolve_entities(state)
    
    async def orchestrate_node(self, state: AgentState) -> AgentState:
        return await self.orchestration_service.orchestrate(state)
    
    async def execute_capability_node(self, state: AgentState) -> AgentState:
        return await self.capability_executor.execute(state)
```

### 2. **OrchestrationService** (services/orchestration_service.py) - ~200 lines
```python
class OrchestrationService:
    """Handles orchestration decisions and context building"""
    
    def __init__(self):
        self.context_builder = OrchestrationContextBuilder()
        self.response_generator = ResponseGenerator()
        self.llm = self._init_orchestrator_llm()
    
    async def orchestrate(self, state: AgentState) -> AgentState:
        # Check limits
        # Build context
        # Get decision
        # Handle response
        # Update state
```

### 3. **OrchestrationContextBuilder** (services/orchestration_context.py) - ~150 lines
```python
class OrchestrationContextBuilder:
    """Builds context for orchestration decisions"""
    
    def build_context(self, state: AgentState) -> str:
        sections = [
            self._build_query_section(state),
            self._build_semantic_section(state),
            self._build_completed_tasks_section(state),
            self._build_capabilities_section()
        ]
        return self._format_sections(sections)
    
    def _build_semantic_section(self, state: AgentState) -> str:
        # Extract entity/concept logic
```

### 4. **ResponseGenerator** (services/response_generator.py) - ~150 lines
```python
class ResponseGenerator:
    """Generates final responses from completed tasks"""
    
    def generate_response(self, state: AgentState, orchestrator_response: Any) -> FinalResponse:
        # All the response generation logic currently in orchestrate_node
```

### 5. **CapabilityExecutor** (services/capability_executor.py) - ~100 lines
```python
class CapabilityExecutor:
    """Executes capabilities and manages task results"""
    
    async def execute(self, state: AgentState) -> AgentState:
        capability_name = state.routing.capability_to_execute
        task = self._get_current_task(state)
        
        capability = self.registry.get(capability_name)
        inputs = capability.build_inputs(task, state)
        result = await capability.execute(inputs)
        
        self._store_result(state, task, result)
        return state
```

### 6. **Delete Redundant Methods**
Remove these entirely (use generic execute_capability_node):
- execute_chat_node (lines 288-355)
- execute_ticketing_data_node (lines 357-426) 
- execute_event_analysis_node (lines 428-497)

## Benefits

1. **Single Responsibility**: Each class has one clear purpose
2. **Testability**: Can unit test each service independently
3. **Maintainability**: Easier to find and fix issues
4. **Reusability**: Services can be used by other components
5. **Readability**: Smaller, focused classes are easier to understand

## Migration Strategy

1. **Phase 1**: Extract ResponseGenerator (most self-contained)
2. **Phase 2**: Extract OrchestrationContextBuilder
3. **Phase 3**: Extract OrchestrationService
4. **Phase 4**: Delete redundant capability execution methods
5. **Phase 5**: Extract remaining services

## Code Quality Improvements

1. **Constants**: Move all magic numbers to class constants
2. **Error Handling**: Consistent error handling patterns
3. **Logging**: Structured logging with context
4. **Type Safety**: Stronger typing throughout
5. **Documentation**: Clear docstrings for each service