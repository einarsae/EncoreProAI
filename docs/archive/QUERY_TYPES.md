# EncoreProAI - Understanding Query Types

## Overview

While our system uses frame-based understanding (not intent routing), it's helpful to understand the different types of queries users might make. These categories are **descriptive, not prescriptive** - the orchestrator makes all decisions based on the complete semantic frame.

## Query Type Categories (For Reference Only)

**MVP Capabilities (Week 1):**
- ChatCapability (emotional support) - CRITICAL
- TicketingDataCapability (data access)
- EventAnalysisCapability (analysis)

**Future Capabilities (Post-MVP):**
- All others marked as "future feature" below

### 1. EXPLORE 📋
**Purpose**: Information about what exists in the system
- System capabilities, schema information, help requests
- Requires actual lookup of schemas, entities, capabilities
- **Examples**: 
  - "What can this system do?"
  - "Which shows do I have?"
  - "What tables are available?"
- **Capabilities**: ExploreCapability (future feature)

### 2. DATA 📊
**Purpose**: Any query requesting measures (revenue, attendance, counts)
- Simple data retrieval with quantifiable metrics
- **Examples**: 
  - "What's the revenue for Gatsby?"
  - "How many tickets sold last month?"
- **Capabilities**: TicketingDataCapability

### 3. ANALYSIS 🧠
**Purpose**: Data analysis requiring computation/comparison
- Complex analysis, calculations, comparisons
- **Examples**: 
  - "Compare revenue trends"
  - "What's our best performing show?"
- **Capabilities**: EventAnalysisCapability

### 4. SEGMENT 👥
**Purpose**: Audience segmentation and customer analysis
- Customer insights, audience analysis, patron behavior
- **Examples**: 
  - "Which customer segments convert best?"
  - "Show me premium ticket buyer behavior"
- **Capabilities**: CustomerSegmentCapability (future feature)

### 5. CAMPAIGN 📢
**Purpose**: Marketing campaign strategy and creation
- Campaign planning, marketing strategy, audience targeting
- **Examples**: 
  - "What campaigns should I run?"
  - "Create a campaign for underperforming shows"
- **Capabilities**: CampaignCapability (future feature)

### 6. STRATEGY 🎯
**Purpose**: High-level business strategy and planning
- Business strategy, portfolio optimization, strategic recommendations
- **Examples**: 
  - "Overall business performance"
  - "Which shows to prioritize next season?"
- **Capabilities**: StrategyCapability (future feature)

### 7. AGENT 🤖
**Purpose**: Proactive agent-driven insights and follow-ups
- AI-driven insights, proactive analysis, background monitoring
- **Examples**: 
  - "Find interesting patterns"
  - "What should I pay attention to?"
- **Capabilities**: ExplorerCapability (future feature)

### 8. AUTOMATION 🔄
**Purpose**: Scheduled/triggered actions
- Scheduled reports, alerts, recurring workflows
- **Examples**: 
  - "Send me daily reports"
  - "Alert when attendance drops below 80%"
- **Capabilities**: AutomationCapability (future feature)

### 9. CHAT 💬
**Purpose**: Conversational interactions and companionship
- Social interactions, acknowledgments, clarifications, emotional support
- **Examples**: 
  - "Thank you"
  - "Hello"
  - "I don't understand"
  - "I'm feeling overwhelmed"
- **Capabilities**: ChatCapability (with empathy)

## How Query Understanding Works

**IMPORTANT**: We do NOT use intent-based routing. Instead:

1. **Frame Extraction** captures the complete semantic meaning:
   - Mentions (entities, concepts, time, modifiers)
   - Relations (how mentions connect)
   - Metadata (confidence, emotional tone)

2. **The Orchestrator** looks at the frame and decides:
   - What information is needed
   - Which capability can provide it
   - How to present the results

3. **Single-Task Execution** means:
   - One decision at a time
   - See results and adapt
   - No predetermined paths

## Why No Intent Routing?

- **Frames are richer** than intent categories
- **More flexible** - handles novel queries naturally
- **Simpler** - no routing rules to maintain
- **More powerful** - true adaptive behavior

## Frame-Based Understanding Example

**Query**: "I'm overwhelmed - show me which shows are underperforming"

**Frame Extracted**:
```python
Frame(
    query="I'm overwhelmed - show me which shows are underperforming",
    entities=["shows"],
    times=[],
    concepts=["overwhelmed", "underperforming"]
)
```

**Orchestrator Decision Process**:
1. Sees emotional mention → Provide supportive response
2. Sees performance concept → Need data analysis
3. Creates task: ChatCapability for emotional support
4. Next loop: Creates task: TicketingDataCapability for data
5. Next loop: Creates task: EventAnalysisCapability for "underperforming"
6. Final: Synthesizes compassionate response with clear insights

## Benefits of Frame-Based Approach

1. **No Rigid Categories**: Every query is understood on its own terms
2. **Contextual Understanding**: Full semantic graph informs decisions
3. **Adaptive Behavior**: System improves without changing routing rules
4. **Handles Complexity**: Multi-faceted queries handled naturally
5. **Emotional Intelligence**: Emotional context is part of the frame

## Key Insight

The query categories above are useful for:
- **Documentation**: Helping humans understand query types
- **Testing**: Ensuring we cover different scenarios
- **Debugging**: Describing what happened

But they are NOT used for:
- **Routing**: The orchestrator decides based on frames
- **Limiting**: Queries can span multiple categories
- **Classification**: No separate intent detection step

The frame IS the understanding. The orchestrator IS the intelligence.