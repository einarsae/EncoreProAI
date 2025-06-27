# EncoreProAI - Glossary

## Core Terminology

### Architecture Components

**Service**: Self-contained data access component (CubeService, EntityResolver, etc.)
- NOT "tool" - we don't use that term
- Services handle direct data operations

**Capability**: Business logic wrapper that uses services
- ChatCapability, TicketingDataCapability, etc.
- Capabilities orchestrate services to fulfill user needs

**Orchestrator**: The single LangGraph node that decides next actions
- NOT "planner" - there is no separate planning phase
- Creates one task at a time with built-in replanning

**Frame**: A fully self-contained semantic context that captures a single, complete unit of meaning
- Includes all necessary context for understanding
- No unresolved references, coreferences, or external dependencies
- This IS the complete understanding - no separate intent classification needed
- Implementation simplified: query text + lists of entities/times/concepts to resolve

### State Management

**State**: What changes during execution (AgentState)
- Grouped into logical sub-states (CoreState, SemanticState, etc.)
- Passed between nodes

**Context**: Shared resources that don't change (AgentContext)
- Services, LLM clients, configuration
- Injected into nodes/capabilities

### Semantic Understanding

**Extracted Items** (formerly Mentions): Things identified for resolution
- Entities: Productions, venues, locations needing database lookup
- Times: Date expressions needing parsing
- Concepts: Terms (including emotions) for memory context
- Stored as simple lists in Frame (implementation detail)

**Relations**: No longer explicitly stored
- Orchestrator infers relationships from query text
- Simplifies extraction and maintenance

**Resolution**: Process of mapping mentions to concrete values
- Entity resolution: text → database record
- Concept resolution: business term → technical measure
- Time resolution: expression → date range

### Execution Pattern

**Single-Task Execution**: Orchestrator creates ONE task at a time
- Sees results and adapts
- No pre-planned multi-step execution
- Built-in replanning

**Orchestration Loop**: The cycle of task → result → next task
- Continues until orchestrator decides to complete
- Each loop has full visibility of previous results

### Important Distinctions

**Services vs Tools**: We use "services" exclusively
**Orchestrator vs Planner**: We use "orchestrator" exclusively  
**Capability vs Tool**: Capabilities USE services, they don't replace them
**Frame vs Intent**: We don't use intent classification - the frame contains complete understanding
**Understanding vs Routing**: Frame-based understanding, not intent-based routing

### Execution Components

**Task**: Single unit of work created by orchestrator
- Has unique ID for referencing
- Contains capability name and inputs
- Can reference previous task results via {{task_id}}

**TaskResult**: Output from executing a task
- Contains task_id, capability used, result data
- Stored in state.execution.completed_tasks
- Can be referenced by subsequent tasks

**Capability Registry**: Central registry of available capabilities
- Maps capability names to implementations
- Used by orchestrator to discover what's possible
- Each capability self-describes its inputs/outputs

### Infrastructure

**LLM Service**: Language model integration
- Used for frame extraction, orchestration, analysis
- Configured via environment variables
- Handles retries and error recovery

**Embedding Service**: Vector embedding generation  
- Used by MemoryService for similarity search
- Typically OpenAI text-embedding-ada-002
- Generates 1536-dimensional vectors