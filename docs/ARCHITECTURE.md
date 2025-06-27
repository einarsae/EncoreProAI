# EncoreProAI - Architecture Details

## Overview

This is an LLM-first architecture with adaptive planning. We extract only what needs resolution, letting the intelligent orchestrator handle the complexity.

## LangGraph-Based Orchestration

The system uses LangGraph for proven workflow orchestration with capability integration:

1. **Frame Extraction**: Extract only entities and concepts that need resolution
2. **Entity Resolution**: Resolve entities to database records (preserving ambiguity)
3. **Concept Resolution**: Resolve concepts using memory-based learning
4. **Orchestration**: LLM creates ONE task at a time with built-in replanning

**Key Insight**: Single-task execution with continuous replanning - the LLM sees results and adapts the plan dynamically!

LangGraph provides:
- ✅ Proven state management (you already have this working)
- ✅ Node-based workflow with clear boundaries
- ✅ Built-in error handling and retries
- ✅ Conditional routing based on state
- ✅ Streaming support for real-time updates

See [QUERY_TYPES.md](./QUERY_TYPES.md) for query type descriptions (reference only).
See [ORCHESTRATION.md](./ORCHESTRATION.md) for implementation details.

## Core Components

### 1. Workflow Structure

```
START → extract_frame → resolve_entities → resolve_concepts → resolve_time → orchestrate → END
                                                                                     ↑__________|
                                                                                   (loop until done)
```

### 2. Simplified Frame Extraction

#### ExtractFrameNode
```python
async def extract_frame_node(state: AgentState) -> AgentState:
    """Extract only what needs resolution - entities and concepts"""
    
    frame = await frame_extractor.extract(state.core.query)
    
    # Frame contains:
    # - entities: List[EntityToResolve] - things like "Chicago", "Gatsby"  
    # - concepts: List[str] - things like "revenue", "overwhelmed"
    
    # Example: "Show me Chicago revenue last month"
    # entities: [EntityToResolve(id="e1", text="Chicago", type="production")]
    # concepts: ["revenue"]
    # (Time expressions handled by orchestrator, not pre-resolved)
    
    state.semantic.frames = [frame]
    state.semantic.current_frame_id = "0"  # Index in frames list
    return state
```

#### ResolveEntitiesNode (With Ambiguity Preservation)
```python
async def resolve_entities_node(state: AgentState) -> AgentState:
    """Resolve entities while preserving ambiguity for orchestrator"""
    
    frame = get_current_frame(state)
    
    for mention in frame.mentions:
        if mention.kind == ENTITY:
            candidates = await entity_resolver.find_candidates(
                text=mention.text,
                entity_type=mention.subtype
            )
            
            if len(candidates) == 1:
                mention.context["resolved_id"] = candidates[0].id
                mention.context["resolution_type"] = "single"
            elif len(candidates) > 1:
                # Preserve ALL candidates for LLM to choose (can select multiple!)
                mention.context["resolution_type"] = "ambiguous"
                mention.context["candidate_entities"] = candidates
                mention.context["selection_hints"] = {
                    "revenue": [c.revenue for c in candidates],
                    "status": [c.status for c in candidates]
                }
    
    return state
```

#### ResolveConceptsNode
```python
async def resolve_concepts_node(state: AgentState) -> AgentState:
    """Resolve concepts using memory-based learning"""
    
    frame = get_current_frame(state)
    
    # Resolve each concept to memory context
    for concept_text in frame.concepts:
        memory_context = await concept_resolver.resolve(concept_text)
        
        resolved_concept = ResolvedConcept(
            id=f"c{len(frame.resolved_concepts)+1}",
            text=concept_text,
            memory_context=MemoryContext(
                concept=concept_text,
                related_queries=memory_context.get("related_queries", []),
                usage_count=memory_context.get("usage_count", 0),
                relevance_score=memory_context.get("relevance_score", 0.5)
            )
        )
        frame.resolved_concepts.append(resolved_concept)
    
    return state

### 3. Orchestration with Single-Task Execution

#### OrchestrateNode (No Separate Planner!)
```python
async def orchestrate_node(state: AgentState) -> AgentState:
    """LLM creates ONE task at a time with built-in replanning"""
    
    frame = get_current_frame(state)
    
    # Handle ambiguous entities
    ambiguous_mentions = [
        m for m in frame.mentions 
        if m.context.get("resolution_type") == "ambiguous"
    ]
    
    orchestration_prompt = f"""
    Query: {state.core.query}
    Frame: {frame}
    
    {f"AMBIGUOUS ENTITIES:" if ambiguous_mentions else ""}
    {format_ambiguous_entities(ambiguous_mentions)}
    
    Completed Tasks:
    {format_completed_tasks(state.execution.completed_tasks)}
    
    Available Capabilities:
    {[cap.describe() for cap in capability_registry.get_all()]}
    
    Create the NEXT SINGLE task or complete.
    
    For ambiguous entities, you can select ONE OR MORE candidates if relevant.
    Reference previous results as {{{{task_id}}}}.
    
    Return: {{"action": "execute", "capability": "...", "task": {{...}}}}
    Or: {{"action": "complete", "response": "...", "assumptions": [...]}}
    """
    
    decision = await llm.orchestrate(orchestration_prompt)
    
    if decision.action == "complete":
        state.core.final_response = {
            "response": decision.response,
            "assumptions": decision.assumptions
        }
        state.routing.next_node = END
    else:
        # Create and execute single task
        task = create_task(decision, state)
        
        # Handle entity disambiguation (can select multiple!)
        if "entity_selection" in decision:
            apply_entity_selection(frame, decision.entity_selection)
        
        # Execute capability
        result = await execute_task(task, state)
        
        # Update state with result
        state.execution.completed_tasks[task.task_id] = result
        
        # Loop back - LLM will see result and decide next step
        state.routing.next_node = "orchestrate"
    
    return state
```

**Key Innovation**: Frame-based orchestration! The orchestrator:
1. Sees the complete semantic frame (not just intent)
2. Understands full context through mentions and relations
3. Decides ONE next action based on this rich understanding
4. Executes and observes results
5. Loops back with new information
6. Adapts strategy based on actual outcomes

**No intent routing! No predetermined flows! Just intelligent decisions based on semantic understanding.**

### 4. Self-Contained Services (NO External Dependencies)

```python
# services/cube_service.py
import httpx
import jwt
from datetime import datetime, timedelta

class CubeService:
    """Self-contained Cube.js integration"""
    def __init__(self, cube_url: str, cube_secret: str):
        self.cube_url = cube_url
        self.cube_secret = cube_secret
    
    def generate_token(self, tenant_id: str) -> str:
        """JWT with tenant isolation - simplified"""
        payload = {
            "sub": tenant_id,
            "tenant_id": tenant_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        return jwt.encode(payload, self.cube_secret, algorithm="HS256")
    
    async def query(self, measures, dimensions, filters, tenant_id):
        """Execute Cube.js query - preserves security concepts"""
        token = self.generate_token(tenant_id)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.cube_url}/cubejs-api/v1/load",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "measures": measures,
                    "dimensions": dimensions,
                    "filters": filters
                }
            )
            return response.json()
```

### 3. Capability Layer (NEW)

```python
class BaseCapability(ABC):
    """Minimal abstraction - no defensive coding"""
    
    @abstractmethod
    def describe(self) -> CapabilityDescription:
        """For LLM understanding"""
        
    @abstractmethod
    async def execute(self, inputs: CapabilityInputs) -> CapabilityResult:
        """Execute with Pydantic models (not dicts)"""
```

### 4. ChatCapability (NEW & CRITICAL)

```python
class ChatCapability(BaseCapability):
    """Empathetic companion for non-strategic conversations"""
    
    async def execute(self, inputs: ChatInputs) -> ChatResult:
        # Provide emotional support
        # Generate follow-up questions
        # Use slightly emotional language
        # Handle companionship needs
```

### 5. Generic Analysis (NOT HARDCODED)

```python
class EventAnalysisCapability(BaseCapability):
    """LLM decides thresholds and criteria"""
    
    async def analyze_performance(self, 
                                  metrics: List[str],
                                  criteria: Dict[str, Any],
                                  comparison_type: str):
        # NO hardcoded find_underperforming(threshold=0.8)
        # LLM determines what "underperforming" means
        # Flexible analysis based on inputs
```

## Data Models (Pydantic v2)

```python
from pydantic import BaseModel, Field

class CapabilityInputs(BaseModel):
    """Base inputs - extend for each capability"""
    user_context: UserContext
    query_context: QueryContext

class CapabilityResult(BaseModel):
    """Standard result format"""
    success: bool
    data: Any  # Actual data model, not dict
    metadata: ResultMetadata
    errors: List[str] = Field(default_factory=list)

class ChatInputs(CapabilityInputs):
    """Chat-specific inputs"""
    message: str
    emotional_context: EmotionalContext
    conversation_history: List[Message]
```

## State Management (MINIMAL)

```python
## State Management (GROUPED ARCHITECTURE)

**Design Philosophy**: Group related state into logical sub-models for clarity and maintainability.

```python
class AgentState(BaseModel):
    """Grouped state architecture - proven to scale"""
    core: CoreState          # Identity, status, messages
    routing: RoutingState    # Next node decisions
    semantic: SemanticState  # Frames with mentions/relations
    execution: ExecutionState # Tasks and typed results
    memory: MemoryState      # References only (no content!)
    debug: Optional[DebugState] = None

class CoreState(BaseModel):
    """Identity and processing status"""
    session_id: str
    user_id: str
    tenant_id: str
    query: str
    status: Literal["processing", "complete", "error"]
    current_node: Optional[str]
    messages: List[Message]
    final_response: Optional[Dict[str, Any]]

class SemanticState(BaseModel):
    """Frame-based semantic understanding"""
    frames: List[Frame]
    current_frame_id: Optional[str]
    
class Frame(BaseModel):
    """Simplified semantic unit for resolution"""
    query: str                    # Original text for this semantic unit
    entities: List[str]           # ["Chicago", "Gatsby"] 
    times: List[str]             # ["last month", "yesterday"]
    concepts: List[str]          # ["revenue", "overwhelmed"]
    
    # Resolutions (populated after extraction)
    resolved_entities: List[ResolvedEntity]  # id, text, candidates
    resolved_times: List[ResolvedTime]      # id, text, date_range
    resolved_concepts: List[ResolvedConcept] # id, text, memory_context

class ExecutionState(BaseModel):
    """Task execution with single-task pattern"""
    completed_tasks: Dict[str, TaskResult]  # task_id -> result
    loop_count: int = 0  # Simple loop protection
    
    # Note: Resolution results now stored in mention.context
    # No separate resolved_entities/concepts/times dicts needed

class MemoryState(BaseModel):
    """Memory and user context references"""
    conversation_history: List[str]  # Recent conversation IDs
    user_preferences: Dict[str, Any]  # How user prefers analysis
    domain_knowledge: Dict[str, Any]  # Theater industry context
```

### Why Grouped State?

1. **Clear Ownership**: Each node knows which sub-state to modify
2. **Type Safety**: Pydantic validates each group independently  
3. **Testability**: Test sub-states in isolation
4. **No Namespace Pollution**: 50+ fields organized logically
5. **Performance**: Load only needed sub-states

### Context (Shared Resources)

```python
class AgentContext(BaseModel):
    """Resources that don't change during execution"""
    tenant_id: str
    llm_services: LLMServices
    data_services: DataServices
    tools: Dict[str, BaseTool]
    config: AgentConfig
```

## Security Architecture (PRESERVED)

### JWT Authentication for Cube.js
```python
# Existing logic preserved:
# - Generate JWT with tenant_id and sub claims
# - 30-minute expiration
# - HS256 signing
# - Strict tenant isolation in Cube.js
```

### Multi-tenant Data Access
- All queries include tenant_id
- Row-level security enforced at Cube.js level
- No data leakage between tenants

## Tool Schema Explanation

The tool schema describes available data to the LLM:

```python
class ToolSchema(BaseModel):
    """What data this tool can provide"""
    entities: List[str]      # ["shows", "venues", "customers"]
    measures: List[str]      # ["amount", "quantity"] 
    dimensions: List[str]    # ["show_name", "venue_name"]
    filters: Dict[str, str]  # {"time": "date range filter"}
```

This helps the LLM understand what queries are possible.

## Knowledge Base Architecture

```python
class KnowledgeBaseTool:
    """Structured knowledge access"""
    
    def __init__(self):
        # Load from YAML files
        self.definitions = load_yaml('concept_definitions_minimal.yaml')
        self.strategies = load_yaml('business_strategies.yaml')
        
    def get_definition(self, term: str):
        # Return business term definition
        # Used by ChatCapability to explain concepts
        
    def get_calculation(self, metric: str):
        # Return how metrics are calculated
        # Helps LLM understand data
```

Knowledge is:
- Loaded from YAML files (maintainable)
- Tenant-agnostic (shared across all)
- Used to enhance LLM understanding

## Testing Strategy (REAL DATA ONLY)

```python
class RealDataTests:
    """No mocks - test with actual database"""
    
    async def test_gatsby_revenue(self):
        result = await capability.execute({
            "show": "Gatsby",
            "metric": "revenue"
        })
        assert result.success
        assert result.data.amount > 0
```

## What We DON'T Need

1. **Performance optimization**: No caching or parallel execution yet
2. **Mock tools**: Never - real data only
3. **Hardcoded methods**: LLM decides analysis approach
4. **Redis**: Not using for now
5. **Complex error handling**: Fail fast approach

## Helper Functions

```python
def get_current_frame(state: AgentState) -> Frame:
    """Safely get current frame"""
    if state.semantic.current_frame_id:
        for frame in state.semantic.frames:
            if frame.frame_id == state.semantic.current_frame_id:
                return frame
        raise ValueError(f"Frame {state.semantic.current_frame_id} not found")
    elif state.semantic.frames:
        return state.semantic.frames[0]
    else:
        raise ValueError("No frames available")

def format_ambiguous_entities(mentions: List[Mention]) -> str:
    """Format ambiguous entities for LLM decision"""
    output = []
    for mention in mentions:
        candidates = mention.context["candidate_entities"]
        output.append(f"""
        "{mention.text}" could be:
        {[f"- {c.name} (revenue: ${c.revenue}, status: {c.status})" for c in candidates]}
        
        You can select ONE OR MORE if relevant to the query.
        """)
    return "\n".join(output)

def resolve_placeholders(inputs: dict, completed_tasks: dict) -> dict:
    """Replace {{task_id}} with actual results"""
    # Implementation handles nested references
```

## Complete Example: Emotional + Data Query

**Query**: "I'm feeling overwhelmed - can you help me understand which shows are underperforming?"

This example shows how frame-based understanding handles mixed emotional and analytical needs without intent routing.

### Resolution Phase:
1. **Extract Frame**: Mentions for "productions", "revenue", "attendance", "trends"
2. **Resolve Entities**: "productions" → all production entities
3. **Resolve Concepts**: "revenue" → ticket_line_items.amount
4. **Resolve Time**: No explicit time, orchestrator will decide

### Orchestration Loops (Frame-Based Decisions):

**Loop 1** (Initial frame analysis):
- Frame shows: emotional mention ("overwhelmed") + performance concept ("underperforming")
- Orchestrator sees emotional need first
- Decision: Execute ChatCapability for emotional support
- Task: Provide empathetic acknowledgment
- Result: "I understand this can feel overwhelming. Let me help you break this down..."

**Loop 2** (Addressed emotion, now data):
- Frame still has: "shows" entity + "underperforming" concept
- Orchestrator knows emotional support provided
- Decision: Execute TicketingDataCapability
- Task: Get performance metrics for all shows
- Result: Revenue and attendance data as t1

**Loop 3** (Have data, need analysis):
- Frame concept "underperforming" needs interpretation
- Orchestrator has raw data, needs analysis
- Decision: Execute EventAnalysisCapability
- Task: Let LLM determine what "underperforming" means and analyze
- Result: Shows below 70% capacity or declining revenue identified

**Loop 4** (Complete with synthesis):
- All frame elements addressed
- Decision: Complete with supportive summary
- Response: Clear, compassionate explanation of findings with specific recommendations

### Key Benefits:
- **Adaptive**: Plan changes based on results
- **No Waste**: Only gets data actually needed
- **Clear Context**: Each decision has full visibility
- **Natural Flow**: Mimics human problem-solving

## Critical Success Factors

1. **Single-Task Execution**: One task at a time with replanning
2. **Preserve Sophisticated Resolution**: Entities, concepts, time, ambiguity
3. **Frame-Driven Understanding**: Mentions + relations guide everything
4. **LLM Orchestration**: No hardcoded flows or plans
5. **100% Test Success**: With real data (Gatsby, Hell's Kitchen, Outsiders)