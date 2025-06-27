# EncoreProAI - Orchestration Pattern

## Overview

Single-task orchestration with continuous replanning. The orchestrator creates ONE task at a time, sees the result, and decides the next step. No predetermined execution plans.

## Core Concept: Frame-Based Orchestration Loop

```
User Query → Extract Frame → Resolve → Orchestrate → Execute Task → Result
                                              ↑                          |
                                              |__________________________|
                                                    (loop until done)
```

**Key Insight**: The orchestrator makes decisions based on the semantic frame, NOT on intent categories or routing rules.

## The Orchestrator Node

```python
async def orchestrate_node(state: AgentState) -> AgentState:
    """Creates ONE task at a time based on semantic frame"""
    
    # Get complete semantic understanding
    frame = get_current_frame(state)
    
    # Build context showing full frame understanding
    orchestration_context = f"""
    Query: {state.core.query}
    
    Semantic Understanding:
    - Mentions: {[f"{m.text} ({m.kind}:{m.subtype})" for m in frame.mentions]}
    - Relations: {[f"{r.subject} {r.relation} {r.object}" for r in frame.relations]}
    - Emotional Context: {frame.metadata.emotional_context}
    - Complexity: {frame.metadata.complexity}
    
    Completed Tasks: {state.execution.completed_tasks}
    
    Available Capabilities: {capability_descriptions}
    
    Based on this semantic understanding, what is the NEXT SINGLE task?
    """
    
    # LLM decides based on frame, not intent categories
    decision = await llm.orchestrate(orchestration_context)
    
    if decision.action == "complete":
        # Done - create final response
        state.core.final_response = format_response(decision)
        state.routing.next_node = END
    else:
        # Execute one task
        task = create_task(decision)
        result = await execute_capability(task, state)
        
        # Store result
        state.execution.completed_tasks[task.id] = result
        
        # Loop back to orchestrate with new information
        state.routing.next_node = "orchestrate"
    
    return state
```

## Key Innovation: Frame-Based Understanding

Traditional intent-based approach:
1. Classify query into intent category
2. Route to predetermined handler
3. Execute fixed flow for that intent
4. Limited ability to handle nuance

Our frame-based approach:
1. Extract complete semantic frame (mentions + relations)
2. Orchestrator sees full understanding
3. Decide ONE next action based on semantic content
4. Execute and observe results  
5. Adapt strategy based on outcomes
6. Repeat until done

**No intent routing! Every query is understood on its own terms.**

## Example: Complex Query Evolution

**Query**: "Compare revenue for top 3 shows and analyze their trends"

### Loop 1: Initial State
```
State: No data yet
Frame: Contains mentions of "revenue", "top 3", "shows", "trends"
Decision: Need revenue data first
Action: Execute TicketingDataCapability for all shows' revenue
```

### Loop 2: Have Revenue Data
```
State: Have revenue for all shows
Previous: Revenue data in completed_tasks
Decision: Can now identify top 3
Action: Execute EventAnalysisCapability to find top 3 by revenue
```

### Loop 3: Have Top 3
```
State: Know which shows are top 3
Previous: Top 3 show IDs identified
Decision: Need trend data for these specific shows
Action: Execute TicketingDataCapability for time-series data
```

### Loop 4: Have All Data
```
State: Have revenue and trends for top 3
Previous: All necessary data collected
Decision: Ready to analyze and respond
Action: Complete with analysis and insights
```

## Handling Ambiguity

When entities have multiple candidates:

```python
# In orchestration context
"Ambiguous Entities Detected:
'Chicago' could be:
- Chicago (Broadway Production) - revenue: $2M, status: active
- Chicago (Tour) - revenue: $500K, status: closed

You can select ONE OR MORE candidates as relevant to the query."

# LLM can decide:
{
    "action": "execute",
    "capability": "ticketing_data",
    "entity_selection": {
        "Chicago": ["prod-123"]  # Chose Broadway version
    }
}
```

## Task Dependencies

Tasks can reference previous results:

```python
{
    "action": "execute",
    "capability": "event_analysis",
    "task": {
        "data": "{{t1}}",  # Reference to previous task result
        "analysis_type": "trend",
        "depends_on": ["t1"]
    }
}
```

## Benefits of This Approach

1. **Adaptive**: Strategy changes based on actual results
2. **Efficient**: Only fetches data actually needed
3. **Transparent**: Each decision has full context
4. **Simple**: No complex planning logic
5. **Natural**: Mimics human problem-solving

## State Context for Orchestration

The orchestrator always sees:
- Original query
- Semantic frame with mentions and relations
- All completed tasks and their results
- Available capabilities
- Current execution state

This full visibility enables intelligent next-step decisions.

## Capability Execution

```python
async def execute_capability(task: Task, state: AgentState) -> TaskResult:
    """Execute a single capability"""
    
    # Get capability
    capability = capability_registry.get(task.capability)
    
    # Build inputs from task and state
    inputs = build_capability_inputs(task.inputs, state)
    
    # Execute
    result = await capability.execute(inputs)
    
    return TaskResult(
        task_id=task.id,
        capability=task.capability,
        result=result,
        timestamp=datetime.now()
    )
```

## When Orchestration Completes

The orchestrator decides to complete when:
- All necessary data has been collected
- Analysis has been performed
- A comprehensive response can be formulated
- Or when user's question has been directly answered

## Error Handling

If a task fails:
- Error is added to state.core.messages
- Orchestrator sees the failure in next loop
- Can decide to:
  - Try alternative approach
  - Complete with partial results
  - Ask for clarification

## No Parallel Execution (By Design)

This architecture deliberately avoids parallel execution complexity:
- One task at a time
- Full visibility of each result
- Decisions based on actual data
- Simpler to understand and debug