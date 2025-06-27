# EncoreProAI - COMPREHENSIVE IMPLEMENTATION TODO

## 🚨 CRITICAL: READ THIS FIRST TO AVOID CATASTROPHIC MISTAKES 🚨

This is a **100% SELF-CONTAINED** implementation. **NEVER** reference or import code from outside the `/encoreproai` folder. This is a complete rewrite, not a refactor!

### What This IS:
- A capability-based architecture with LangGraph orchestration
- Single-task execution with continuous replanning (NO predetermined plans)
- LLM-first design where the AI decides analysis approaches
- Empathetic chat companion for emotional support
- Real data only (Gatsby, Hell's Kitchen, Outsiders)

### What This is NOT:
- NOT a bridge to existing code (we tried that, it failed!)
- NOT using tools from parent directory
- NOT using external databases (PostgreSQL + pgvector only)
- NOT hardcoding analysis thresholds
- NOT creating mock data or fake responses

### Architecture Summary:
```
Query → Extract Frame → Resolve (Entities/Concepts/Time) → Orchestrate → Execute ONE Task → Loop
        (semantic understanding)                          (uses frame, not intent)              |
                                                                  ↑                           |
                                                                  |___________________________|
```

**KEY INSIGHT**: The frame IS the complete understanding. No separate intent classification!

## Day 1: Foundation Setup (NO EXTERNAL DEPENDENCIES!)

### Morning (4 hours)

#### 1. Docker Environment Setup
```yaml
# docker-compose.yml - SELF-CONTAINED!
services:
  postgres:
    image: pgvector/pgvector:15-pg
    environment:
      POSTGRES_DB: encoreproai
      POSTGRES_USER: encore
      POSTGRES_PASSWORD: secure_password
    volumes:
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
```

**Tasks:**
- [ ] Create docker-compose.yml with PostgreSQL + pgvector ONLY
- [ ] Create init.sql with entities table and pg_trgm extension
- [ ] Add .env file with Cube.js URL and secret
- [ ] Test containers start successfully
- [ ] Verify pgvector and pg_trgm extensions work

#### 2. Project Structure Creation
```
encoreproai/
├── services/          # Self-contained services (NO bridges!)
│   ├── cube_service.py      # Direct HTTP to Cube.js with JWT
│   ├── entity_resolver.py   # PostgreSQL trigram search
│   ├── concept_resolver.py  # Hardcoded mappings for MVP
│   ├── time_resolver.py     # LLM-based parsing
│   └── memory_service.py    # PostgreSQL + pgvector
├── capabilities/      # Business logic wrappers
│   ├── base.py            # BaseCapability interface
│   ├── chat.py            # ChatCapability (CRITICAL!)
│   ├── ticketing_data.py  # TicketingDataCapability
│   └── event_analysis.py  # EventAnalysisCapability
├── workflow/          # LangGraph implementation
│   ├── nodes.py           # All workflow nodes
│   ├── state.py           # State definitions
│   └── graph.py           # Workflow definition
├── models/           # Pydantic v2 models
│   ├── frame.py          # Frame, Mention, Relation
│   ├── state.py          # AgentState and sub-states
│   └── capabilities.py   # Input/output models
└── tests/            # Real data tests ONLY
```

**Tasks:**
- [ ] Create all directories
- [ ] Create __init__.py files
- [ ] Set up Python environment with requirements.txt
- [ ] Install: langchain, langgraph, pydantic==2.5.0, httpx, asyncpg, pgvector

#### 3. Core Service Implementation

**CubeService (services/cube_service.py):**
```python
import httpx
import jwt
from datetime import datetime, timedelta

class CubeService:
    """Direct HTTP client to Cube.js - NO external dependencies!"""
    
    def __init__(self, cube_url: str, cube_secret: str):
        self.cube_url = cube_url
        self.cube_secret = cube_secret
    
    def generate_token(self, tenant_id: str) -> str:
        """Generate JWT with tenant isolation"""
        payload = {
            "sub": tenant_id,
            "tenant_id": tenant_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(minutes=30)
        }
        return jwt.encode(payload, self.cube_secret, algorithm="HS256")
    
    async def query(self, measures, dimensions, filters, tenant_id):
        """Execute Cube.js query with minimal error handling"""
        token = self.generate_token(tenant_id)
        
        # Only catch network-specific issues
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.cube_url}/cubejs-api/v1/load",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "measures": measures,
                    "dimensions": dimensions,
                    "filters": filters
                }
            )
            response.raise_for_status()  # Let HTTP errors bubble up
            return response.json()
```

**Tasks:**
- [ ] Implement CubeService with JWT generation
- [ ] Implement EntityResolver with trigram search (based on old EntityLookupStore)
- [ ] Create entity population script (import from Cube.js like old system)
- [ ] Set up entities table with pg_trgm extension and score boosting
- [ ] Create enhanced memory-based concept resolution (combining patterns + learning)
  ```python
  # Enhanced ConceptResolver with pattern learning
  class ConceptResolver:
      def __init__(self):
          self.base_patterns = INITIAL_PATTERNS  # From old system analysis
          self.memory_service = MemoryService()  # Learn new patterns
      
      async def resolve_concept(self, text, context):
          # 1. Check learned patterns first (from memory)
          learned = await self.memory_service.search_concept_patterns(text, context)
          if learned and learned[0].confidence > 0.9:
              return learned[0]
              
          # 2. Try base patterns (no LLM call needed)
          base_match = self.match_base_patterns(text, context)
          if base_match and base_match.confidence > 0.8:
              # Store successful pattern for learning
              await self.memory_service.store_pattern_success(text, context, base_match)
              return base_match
              
          # 3. Only use LLM for truly ambiguous cases
          if self.is_ambiguous(text, context):
              llm_result = await self.llm_resolve(text, context)
              # Store LLM result for future pattern learning
              await self.memory_service.store_concept_resolution(text, context, llm_result)
              return llm_result
              
          return None  # No match found
  ```
- [ ] Implement TimeResolver using LLM  
- [ ] Test each service independently

### Afternoon (4 hours)

#### 4. Database Setup

**Entities Table Schema (Based on Old System):**
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE entities (
    tenant_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tenant_id, entity_type, id)
);

CREATE INDEX idx_entities_trigram ON entities USING gin(name gin_trgm_ops);
CREATE INDEX idx_entities_type_tenant ON entities(tenant_id, entity_type);

-- Optional for memory service
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(1536),
    metadata JSONB,
    user_id TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Tasks:**
- [ ] Create entities table with proper indexes
- [ ] Insert test data for Gatsby, Hell's Kitchen, Outsiders
- [ ] Test trigram similarity with "SELECT similarity(name, 'Chicago') FROM entities"
- [ ] Implement score transformation: 0.3-0.7 → 0.5-1.0
- [ ] Verify ambiguous queries return multiple candidates

#### 5. Service Testing

**Test Scenarios:**
- [ ] CubeService: Generate valid JWT and make test query
- [ ] EntityResolver: Search "Chicago" returns both Broadway and Tour
- [ ] ConceptResolver: "revenue" maps to "ticket_line_items.amount"
- [ ] TimeResolver: "last month" returns correct date range
- [ ] All services handle errors gracefully

## Day 2: Semantic Understanding Pipeline

### Morning (4 hours)

#### 1. Frame Extraction Implementation

**CRITICAL CONCEPT**: Frame = Simplified extraction for resolution
```python
class Frame:
    query: str                    # Original text for this semantic unit
    entities: List[str]           # ["Chicago", "Gatsby"] 
    times: List[str]             # ["last month", "yesterday"]
    concepts: List[str]          # ["revenue", "overwhelmed"]
    
    # Resolutions (populated after extraction)
    resolved_entities: List[ResolvedEntity]  # id, text, candidates
    resolved_times: List[ResolvedTime]      # id, text, date_range
    resolved_concepts: List[ResolvedConcept] # id, text, memory_context
```

**Tasks:**
- [x] Implement frame_extractor.py with simplified LLM prompt
- [x] Extract only what needs resolution (entities, times, concepts)
- [x] Remove complex Mentions/Relations structure
- [x] Handle coreferences by keeping related content in same frame
- [x] Test frame extraction with all test queries

#### 2. Pydantic Models

**State Architecture (CRITICAL - Use Grouped State!):**
```python
class AgentState(BaseModel):
    """Main state - passed between nodes"""
    core: CoreState          # Session, query, messages
    routing: RoutingState    # Next node decision
    semantic: SemanticState  # Frames with mentions
    execution: ExecutionState # Tasks and results
    memory: MemoryState      # Memory references

class SemanticState(BaseModel):
    """All semantic understanding"""
    frames: List[Frame]
    current_frame_id: Optional[str]

class Frame(BaseModel):
    """Complete semantic understanding - NO SEPARATE INTENT!"""
    mentions: List[Mention]    # All semantic units
    relations: List[Relation]  # How they connect
    metadata: FrameMetadata    # Confidence, emotion, complexity
```

**Tasks:**
- [ ] Create all state models with proper typing
- [ ] Create Frame, Mention, Relation models
- [ ] Create capability input/output models
- [ ] Test model validation and serialization
- [ ] Ensure no circular imports

### Afternoon (4 hours)

#### 3. Resolution Node Implementation

**ExtractFrameNode:**
- [ ] Takes query, returns Frame with mentions/relations
- [ ] Handles complex queries with multiple concepts
- [ ] Identifies coreference for SAME_AS relations
- [ ] Adds to state.semantic.frames

**ResolveEntitiesNode (PRESERVE AMBIGUITY!):**
```python
# WRONG:
if len(candidates) > 1:
    mention.context["resolved_id"] = candidates[0].id  # NO!

# RIGHT:
if len(candidates) > 1:
    mention.context["resolution_type"] = "ambiguous"
    mention.context["candidate_entities"] = candidates  # ALL of them!
```

**Tasks:**
- [ ] Implement ExtractFrameNode
- [ ] Implement ResolveEntitiesNode with ambiguity preservation
- [ ] Implement ResolveConceptsNode with SAME_AS handling
- [ ] Implement ResolveTimeNode with context awareness
- [ ] Test each node independently

#### 4. Pipeline Testing

**Test Queries:**
- [ ] "Show me Chicago revenue" → Ambiguous entity preserved
- [ ] "How did it do last month?" → SAME_AS relation works
- [ ] "Compare top 3 shows" → Multiple mentions extracted
- [ ] "Revenue vs attendance" → Multiple concepts resolved
- [ ] Error handling for malformed queries

## Day 3: ChatCapability - THE MOST CRITICAL COMPONENT!

### Morning (4 hours)

#### 1. ChatCapability Implementation

**This is NOT optional! Users need emotional support:**
```python
class ChatCapability(BaseCapability):
    """Provide companionship and emotional support"""
    
    async def execute(self, inputs: ChatInputs) -> ChatResult:
        # Detect emotional state
        emotional_keywords = ["overwhelmed", "stressed", "confused", "frustrated", "help"]
        needs_support = any(word in inputs.message.lower() for word in emotional_keywords)
        
        # Generate empathetic response
        prompt = f"""
        User message: {inputs.message}
        Emotional context: {inputs.emotional_context}
        
        Respond with warmth and understanding.
        If the user seems stressed, acknowledge their feelings first.
        Use slightly emotional language (not robotic!).
        Always end with ONE helpful follow-up question.
        
        Be a supportive companion, not just an analyst.
        """
        
        response = await llm.generate(prompt)
        
        return ChatResult(
            response=response.content,
            follow_up_questions=response.questions,
            emotional_tone=detected_tone
        )
```

**Tasks:**
- [ ] Create ChatCapability with emotional detection
- [ ] Implement warm, empathetic response generation
- [ ] Add follow-up question generation
- [ ] Handle transitioning between chat and data queries
- [ ] Test with stressed user scenarios

#### 2. Emotional Support Features

**Key Behaviors:**
- [ ] Acknowledge feelings: "I understand this can be overwhelming..."
- [ ] Offer support: "Let's break this down together..."
- [ ] Simplify complex data: "The key thing to focus on is..."
- [ ] Encourage: "You're asking great questions..."
- [ ] Follow up: "Would it help if I explained...?"

### Afternoon (4 hours)

#### 3. Chat Testing Scenarios

**MUST HANDLE:**
- [ ] "I'm so overwhelmed with all these numbers"
- [ ] "This is confusing, I don't know where to start"
- [ ] "Help me understand what's important"
- [ ] "I'm stressed about our performance"
- [ ] "Can you just talk me through this?"

#### 4. Integration

- [ ] Orchestrator detects emotional mentions in frame
- [ ] Handle mixed conversations (emotional + data)
- [ ] Smooth transitions between modes
- [ ] Maintain context across conversation
- [ ] Test end-to-end chat flows

## Day 4: LangGraph Orchestration

### Morning (4 hours)

#### 1. Workflow Setup

**Graph Definition (workflow/graph.py):**
```python
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("extract_frame", extract_frame_node)
workflow.add_node("resolve_entities", resolve_entities_node)
workflow.add_node("resolve_concepts", resolve_concepts_node)
workflow.add_node("resolve_time", resolve_time_node)
workflow.add_node("orchestrate", orchestrate_node)

# Add edges
workflow.add_edge("extract_frame", "resolve_entities")
workflow.add_edge("resolve_entities", "resolve_concepts")
workflow.add_edge("resolve_concepts", "resolve_time")
workflow.add_edge("resolve_time", "orchestrate")

# Conditional edge from orchestrate
workflow.add_conditional_edges(
    "orchestrate",
    lambda x: x.routing.next_node,
    {"orchestrate": "orchestrate", END: END}
)

workflow.set_entry_point("extract_frame")
app = workflow.compile()
```

**Tasks:**
- [ ] Create workflow definition
- [ ] Implement all nodes
- [ ] Set up proper routing
- [ ] Add error handling
- [ ] Test workflow execution

#### 2. Orchestrator Node - THE BRAIN!

**CRITICAL: Single-task execution with replanning!**
```python
async def orchestrate_node(state: AgentState) -> AgentState:
    """Creates ONE task at a time, sees result, adapts"""
    
    # Simple loop protection - no try/catch
    if state.execution.loop_count > 10:
        state.core.final_response = {
            "error": "Too many steps required",
            "partial_results": state.execution.completed_tasks
        }
        state.routing.next_node = END
        return state
    
    state.execution.loop_count += 1
    
    # NO pre-planned execution! Just: What's the NEXT SINGLE thing to do?
    decision = await llm.orchestrate(build_orchestration_context(state))
    
    if decision.action == "complete":
        state.core.final_response = format_response(decision)
        state.routing.next_node = END
    else:
        # ONE task only! Let failures bubble up
        task = create_single_task(decision)
        result = await execute_capability(task, state)  # No try/catch here
        state.execution.completed_tasks[task.id] = result
        state.routing.next_node = "orchestrate"  # Loop back!
    
    return state
```

**Tasks:**
- [ ] Implement orchestrate_node with single-task pattern
- [ ] Create orchestration prompt with full context
- [ ] Handle ambiguous entity selection
- [ ] Implement task creation and execution
- [ ] Add result referencing ({{task_id}})

### Afternoon (4 hours)

#### 3. Orchestration Features

**Ambiguity Handling:**
```python
# In orchestration prompt:
"""AMBIGUOUS ENTITIES DETECTED:
'Chicago' could be:
- Chicago (Broadway) - revenue: $2M, status: active
- Chicago (Tour) - revenue: $500K, status: completed

You can select ONE OR MORE candidates as relevant."""
```

**Tasks:**
- [ ] Format ambiguous entities for LLM decision
- [ ] Implement entity selection in task
- [ ] Handle task dependencies with {{task_id}}
- [ ] Track assumptions made
- [ ] Test replanning when results unexpected

#### 4. Orchestration Testing

**Test Scenarios:**
- [ ] Simple query: "Show revenue for Gatsby"
- [ ] Ambiguous: "Show Chicago performance" (which one?)
- [ ] Multi-step: "Top 3 shows by revenue, then analyze trends"
- [ ] Replanning: Query that requires strategy change
- [ ] Error recovery: Handle capability failures

## Day 5: Data Capabilities

### Morning (4 hours)

#### 1. TicketingDataCapability

**NO HARDCODED METHODS!**
```python
class TicketingDataCapability(BaseCapability):
    """Flexible data access - LLM decides query structure"""
    
    async def execute(self, inputs: TicketingDataInputs) -> TicketingDataResult:
        # LLM has already decided:
        # - What measures to query
        # - What dimensions to use
        # - What filters to apply
        # - How to aggregate
        
        # We just execute what was requested
        cube_response = await self.cube_service.query(
            measures=inputs.measures,
            dimensions=inputs.dimensions,
            filters=inputs.filters,
            tenant_id=inputs.tenant_id
        )
        
        return TicketingDataResult(
            data=transform_cube_response(cube_response),
            query_metadata=build_metadata(inputs)
        )
```

**Tasks:**
- [ ] Implement flexible query execution
- [ ] NO methods like get_revenue() or find_top_shows()
- [ ] Handle multi-dimensional queries
- [ ] Format results appropriately
- [ ] Test with various query types

#### 2. EventAnalysisCapability

**LLM Decides Everything:**
```python
# WRONG:
def find_underperforming(self, threshold=0.8):  # NO!
    return [show for show in shows if show.revenue < avg * threshold]

# RIGHT:
async def analyze(self, criteria_from_llm):
    # LLM decided what "underperforming" means
    # Could be: below average, declining trend, vs similar shows, etc.
```

**Tasks:**
- [ ] Generic analysis methods only
- [ ] Pattern detection without hardcoded patterns
- [ ] Comparison without fixed thresholds
- [ ] Let LLM interpret "underperforming", "successful", etc.
- [ ] Test flexible analysis

### Afternoon (4 hours)

#### 3. Capability Testing

**Real Queries to Test:**
- [ ] "Revenue for all shows"
- [ ] "Which shows need attention?" (LLM decides criteria)
- [ ] "Compare Gatsby to Hell's Kitchen"
- [ ] "Show attendance trends"
- [ ] "Find successful venues" (LLM defines success)

#### 4. Integration Testing

**End-to-End Flows:**
- [ ] Chat → Data query → Analysis → Chat
- [ ] Complex multi-step analysis
- [ ] Ambiguous entity handling
- [ ] Performance with real Cube.js
- [ ] Assumption tracking in responses

## Day 6: Intelligence & Memory System

### Morning (4 hours)

#### 1. Enhanced Memory Service (PRIORITY - Not Optional!)

**Learning-Based Resolution Memory:**
```python
class MemoryService:
    """Adaptive memory system that learns from successful resolutions"""
    
    # Pattern Learning (inspired by old ContextualConceptMapper)
    async def store_concept_pattern(self, pattern: str, concept: str, context: str, success_rate: float):
        # "how many (people|attendees)" → attendance (95% success)
        
    async def store_entity_disambiguation(self, raw_term: str, resolved_entity: str, context_clues: List[str]):
        # "Chicago" + ["revenue", "performance"] → "prod_chicago_broadway"
        
    async def store_resolution_analytics(self, resolution_type: str, raw_input: str, outcome: str):
        # Track what works for continuous improvement
        
    # User Experience Memory  
    async def store_user_preference(self, user_id: str, preference: str, context: str):
        # "This user prefers monthly comparisons"
        
    async def store_domain_knowledge(self, concept: str, explanation: str):
        # "Broadway shows typically aim for 80%+ capacity for good performance"
        
    # Memory Retrieval for Intelligence
    async def search_concept_patterns(self, text: str, context: str) -> List[ConceptMatch]:
        # Find learned patterns for concept resolution
        
    async def search_disambiguation_history(self, entity_text: str, context: str) -> List[EntityCandidate]:
        # Find similar disambiguation cases
        
    async def get_orchestration_context(self, query: str, user_id: str):
        # Enhanced context with learned patterns
        user_context = await self.search_similar(query, user_id=user_id)
        domain_context = await self.search_similar(query, user_id="institutional")
        pattern_context = await self.search_relevant_patterns(query)
        return {"user": user_context, "domain": domain_context, "patterns": pattern_context}
```

**Enhanced Memory Schema:**
```sql
-- Base memory table (already exists)
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    user_id TEXT,
    tenant_id TEXT DEFAULT 'default',
    memory_type TEXT DEFAULT 'conversation',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Resolution analytics for learning
CREATE TABLE resolution_analytics (
    id SERIAL PRIMARY KEY,
    resolution_type TEXT NOT NULL,  -- 'concept', 'entity', 'time'
    raw_input TEXT NOT NULL,
    resolved_output TEXT NOT NULL,
    context_data JSONB,
    confidence_score REAL,
    success_indicators JSONB,
    user_feedback TEXT,
    tenant_id TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Pattern success tracking
CREATE TABLE pattern_success (
    id SERIAL PRIMARY KEY,
    pattern_text TEXT NOT NULL,
    pattern_type TEXT NOT NULL,  -- 'concept_pattern', 'entity_disambiguation'
    target_concept TEXT,
    context_clues JSONB,
    usage_count INTEGER DEFAULT 1,
    success_count INTEGER DEFAULT 1,
    last_used TIMESTAMP DEFAULT NOW(),
    tenant_id TEXT
);
```

**Tasks:**
- [ ] Implement enhanced memory tables with resolution analytics
- [ ] Add pattern learning from old ContextualConceptMapper insights
- [ ] Store successful concept → field mappings
- [ ] Track entity disambiguation patterns  
- [ ] Implement confidence-based pattern selection
- [ ] Add query pattern recognition and success tracking
- [ ] Populate initial patterns from old system analysis:
  ```python
  INITIAL_PATTERNS = {
      "attendance_patterns": [
          {"pattern": r"how many (people|attendees|customers)", "concept": "attendance", "confidence": 0.9},
          {"pattern": r"(audience|patron|visitor) count", "concept": "attendance", "confidence": 0.85}
      ],
      "revenue_patterns": [
          {"pattern": r"(revenue|sales|income|gross)", "concept": "revenue", "confidence": 0.95},
          {"pattern": r"how much (money|revenue|sales)", "concept": "revenue", "confidence": 0.9}
      ],
      "performance_patterns": [
          {"pattern": r"how did .* (perform|do)", "concepts": ["revenue", "attendance"], "confidence": 0.8}
      ]
  }
  ```
- [ ] Test pattern learning and recall

#### 2. Final Features

**Assumption Sharing:**
```json
{
  "response": "Based on the data, Gatsby is your top performer...",
  "assumptions": [
    "Used revenue as the success metric",
    "Compared last 30 days of data",
    "Included only Broadway productions"
  ]
}
```

**Tasks:**
- [ ] Add assumption tracking to responses
- [ ] Improve error messages
- [ ] Add query clarification when needed
- [ ] Format responses nicely
- [ ] Test user experience

### Afternoon (4 hours)

#### 3. Bug Fixes

**Priority Order:**
- [ ] Critical: ChatCapability must work perfectly
- [ ] Critical: Basic queries must return data
- [ ] Important: Ambiguity handling
- [ ] Nice: Performance optimizations
- [ ] Optional: Additional capabilities

#### 4. Performance

- [ ] Optimize slow database queries
- [ ] Check LLM response times
- [ ] Validate memory usage
- [ ] Test concurrent requests
- [ ] Add basic caching if needed

## Day 7: Documentation & Demo

### Morning (4 hours)

#### 1. Documentation Updates

**README.md Must Include:**
- [ ] Clear setup instructions
- [ ] Architecture overview
- [ ] Example queries
- [ ] How ChatCapability works
- [ ] NO references to old architecture!

#### 2. Demo Preparation

**Demo Scenarios:**
1. Stressed user gets emotional support
2. Ambiguous query handled gracefully
3. Complex analysis with replanning
4. Mix of chat and data queries
5. Real results from real data

**Tasks:**
- [ ] Create demo script
- [ ] Prepare example queries
- [ ] Test full demo flow
- [ ] Create backup plans
- [ ] Practice presentation

### Afternoon (4 hours)

#### 3. Final Testing

**Critical Test Suite:**
- [ ] All ChatCapability scenarios
- [ ] Basic data queries
- [ ] 100% on all test_queries.md
- [ ] Ambiguous entity handling
- [ ] Multi-step orchestration
- [ ] Error recovery

#### 4. Deployment Preparation

- [ ] Production docker-compose
- [ ] Environment configuration
- [ ] Health check endpoints
- [ ] Monitoring setup
- [ ] Deployment documentation

## 🚨 CRITICAL REMINDERS 🚨

### Architecture Rules:
1. **Single-task orchestration** - NO multi-step plans!
2. **Preserve ambiguity** - Let orchestrator choose entities
3. **LLM decides analysis** - NO hardcoded thresholds
4. **Frame-based understanding** - Complete semantic graph
5. **Real data only** - NO mocks ever!
6. **No intent routing** - Orchestrator uses frames directly
7. **Sparse error handling** - Only catch at boundaries

### Error Handling Rules:
1. **Fail fast and honest** - Let real errors bubble up
2. **Only catch at boundaries** - API endpoints and network calls
3. **NO defensive programming** - Don't check if things exist
4. **NO silent failures** - If it breaks, we want to know
5. **NO generic error messages** - "An error occurred" is useless
6. **Simple safeguards only** - Loop counters, not circuit breakers

### Common Mistakes to Avoid:
1. ❌ Importing from parent directory
2. ❌ Creating bridges to old code
3. ❌ Hardcoding analysis methods
4. ❌ Skipping ChatCapability
5. ❌ Using mock data
6. ❌ Creating predetermined execution plans
7. ❌ Using ClickHouse for vectors
8. ❌ Using wrong state names (use "AgentState" for main state)

### If Behind Schedule:
1. **MUST HAVE**: ChatCapability + TicketingDataCapability
2. **SHOULD HAVE**: Full orchestration loop
3. **NICE TO HAVE**: Memory, additional capabilities
4. **CAN SKIP**: Complex ambiguity handling, optimization

### Success Criteria:
✅ User can have emotional conversation
✅ System queries real Cube.js data
✅ Orchestrator adapts based on results
✅ All code in encoreproai/ folder
✅ Delivered in one week

## Test Queries for Each Day:

**Day 1**: "SELECT similarity(name, 'Chicago') FROM entities;"
**Day 2**: "Extract frame from: Show me Chicago revenue"
**Day 3**: "I'm feeling overwhelmed with these numbers"
**Day 4**: "Which shows are underperforming?" (watch orchestration loop)
**Day 5**: "Compare Gatsby and Hell's Kitchen attendance"
**Day 6**: "What should I focus on today?"
**Day 7**: Full demo with all capabilities

## Final Checklist Before Starting:
- [ ] Deleted all references to old code
- [ ] Have clean encoreproai/ folder
- [ ] Understanding single-task orchestration
- [ ] Know ChatCapability is critical
- [ ] Ready to use real data only

GOOD LUCK! Remember: Working code > Perfect architecture!

## Advanced Features for Later

### EventAnalysisCapability Enhancements
- [ ] Use LLM_PREMIUM (OpenAI) for high-quality analysis
- [ ] Implement data summarization for large datasets instead of passing raw text
- [ ] Add data querying tools within EAC for progressive analysis
- [ ] Include "suggest_visualization" field that recommends chart types without generating
- [ ] Start with hardcoded analysis types, then move to dynamic memory-based patterns
- [ ] Allow users to teach new analysis types through conversation

### Agent Dashboards
- [ ] Create "agent dashboards" that expose analysis insights to managers
- [ ] Provide executive briefings of AI-discovered patterns
- [ ] Real-time visibility into what the AI is learning

### Memory Recognition and Storage
- [ ] Detect when users are providing important information
- [ ] Confidence scoring for user statements
- [ ] Pattern recognition for business rules/preferences
- [ ] Categorize memories (preferences, rules, insights, corrections)
- [ ] Time-decay for relevance
- [ ] Contradiction resolution

### Collective Intelligence
- [ ] How do collective memories become institutional knowledge?
- [ ] Aggregate patterns across tenants (privacy-preserving)
- [ ] Industry benchmarks from anonymized data
- [ ] "This pattern is seen across 73% of similar venues"
- [ ] Shared learning without sharing data