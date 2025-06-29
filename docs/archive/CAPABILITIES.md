# EncoreProAI - Capability Specifications

## Overview

Capabilities wrap existing tools with business logic. The LLM decides how to use them - we don't hardcode specific analysis methods.

## Base Capability Interface

```python
from pydantic import BaseModel
from abc import ABC, abstractmethod

class CapabilityDescription(BaseModel):
    name: str
    purpose: str
    inputs: Dict[str, str]
    outputs: Dict[str, str]
    examples: List[str]

class BaseCapability(ABC):
    @abstractmethod
    def describe(self) -> CapabilityDescription:
        """For LLM understanding"""
        
    @abstractmethod
    async def execute(self, inputs: BaseModel) -> BaseModel:
        """Execute with Pydantic models"""
```

## How Capabilities Are Selected

The orchestrator selects capabilities based on the semantic frame content:

**Frame Analysis → Capability Selection:**
- Emotional mentions (stressed, overwhelmed) → ChatCapability
- Entity mentions + metric concepts → TicketingDataCapability
- Comparison relations between entities → EventAnalysisCapability
- Customer/audience mentions → CustomerSegmentCapability
- Strategy/planning concepts → StrategyCapability

**Key Point**: Selection is dynamic based on frame content, not predetermined routing!

## Core Capabilities

### 1. ChatCapability (NEW - CRITICAL)

**Purpose**: Provide empathetic companionship and non-strategic conversation

```python
class ChatCapability(BaseCapability):
    """AI companion for emotional support and conversation"""
    
    def describe(self):
        return CapabilityDescription(
            name="Chat",
            purpose="Provide companionship, emotional support, and natural conversation",
            inputs={
                "message": "User's message",
                "emotional_context": "Current emotional state",
                "conversation_history": "Previous messages"
            },
            outputs={
                "response": "Empathetic response with slight emotion",
                "follow_up_questions": "Suggested questions to continue conversation",
                "emotional_tone": "Detected emotional context"
            },
            examples=[
                "I'm feeling overwhelmed with these numbers",
                "Tell me about the theater industry",
                "What should I focus on today?"
            ]
        )
    
    async def execute(self, inputs: ChatInputs) -> ChatResult:
        # Provide emotional support
        # Generate engaging follow-ups
        # Use warm, slightly emotional language
```

### 2. TicketingDataCapability

**Purpose**: Generate sophisticated Cube.js queries using ALL available features

```python
class TicketingDataCapability(BaseCapability):
    """LLM-powered Cube.js query generation with full feature support"""
    
    def __init__(self):
        self.cube_service = CubeService()
        self.cube_meta_service = CubeMetaService()
        self.llm = ChatOpenAI(model=os.getenv("LLM_STANDARD"), temperature=0.2)
        
    def describe(self):
        return CapabilityDescription(
            name="TicketingData",
            purpose="Generate sophisticated Cube.js queries with all available features",
            inputs={
                "query_request": "Natural language data request",
                "entities": "Resolved entities with IDs",
                "time_context": "Time period expressions",
                "comparison_type": "Type of comparison needed"
            },
            outputs={
                "data": "DataPoints with measures and dimensions",
                "query_description": "What the query accomplishes",
                "key_findings": "Notable patterns in data",
                "metadata": "Query details and schema info"
            }
        )
    
    async def execute(self, inputs: TicketingDataInputs) -> TicketingDataResult:
        """Generate and execute sophisticated Cube.js queries"""
        # 1. Load full schema context
        # 2. Use LLM to generate query with:
        #    - compareDateRange for time comparisons
        #    - Nested AND/OR filters
        #    - Time granularity (hour, day, week, month)
        #    - Post-aggregation filters
        #    - Drilldowns
        #    - Entity ID-based filtering
        # 3. Execute and format results
```

### 3. EventAnalysisCapability

**Purpose**: Generic analysis without hardcoded thresholds

```python
class EventAnalysisCapability(BaseCapability):
    """Flexible event analysis - LLM decides approach"""
    
    async def analyze_performance(self,
                                  data_points: List[DataPoint],
                                  analysis_criteria: AnalysisCriteria,
                                  context: AnalysisContext) -> AnalysisResult:
        """
        NOT: find_underperforming(threshold=0.8)
        
        Instead: LLM provides criteria like:
        - "Shows below average by 20%"
        - "Venues with declining trends"
        - "Compare to similar shows"
        """
        
    async def identify_patterns(self,
                               dataset: Dataset,
                               pattern_type: str,
                               constraints: Dict) -> PatternResult:
        """
        Generic pattern detection
        LLM decides what patterns to look for
        """
```

### 4. MemoryCapability

**Purpose**: Vector-based memory using PostgreSQL + pgvector

```python
class MemoryCapability(BaseCapability):
    """Vector memory system with semantic search"""
    
    def __init__(self):
        self.memory_service = MemoryService()  # PostgreSQL + pgvector
        
    async def remember(self, 
                      memory_type: MemoryType,
                      content: str,
                      importance: float) -> None:
        """Store with vector embeddings"""
        
    async def recall(self,
                    query: str,
                    memory_types: List[MemoryType],
                    limit: int = 5) -> List[Memory]:
        """Retrieve using vector similarity search"""
```


## Key Design Decisions

### 1. LLM-Driven Analysis
Instead of:
```python
def find_underperforming(threshold=0.8):  # NO!
```

We have:
```python
async def analyze(criteria_from_llm):  # YES!
```

### 2. Generic Methods
The LLM decides:
- What "underperforming" means
- Which metrics to compare
- What time periods to analyze
- How to segment data

### 3. Self-Contained Services
All capabilities use direct service implementations:
- CubeService (with JWT auth)
- EntityResolver (with trigram similarity and ambiguity handling)
- MemoryService (with PostgreSQL+pgvector)
- ConceptResolver (with specificity scoring)
- TimeResolver (with LLM parsing)

## Capability Inputs/Outputs

All use Pydantic v2 models:

```python
class AnalysisRequest(BaseModel):
    """Input for analysis capabilities"""
    query_intent: str
    entities: List[ResolvedEntity]
    time_context: TimeContext
    analysis_type: str
    user_context: UserContext

class AnalysisResult(BaseModel):
    """Output from analysis capabilities"""
    data: DataFrame  # Actual data
    insights: List[Insight]
    visualizations: List[ChartSpec]
    assumptions: List[Assumption]  # What we assumed
    confidence: float
```

## Python Code Execution

Yes, allow the model to use Python for analysis:

```python
class PythonAnalysisCapability(BaseCapability):
    """Execute Python code for complex analysis"""
    
    async def execute_analysis(self, 
                              data: DataFrame,
                              analysis_code: str) -> AnalysisResult:
        """
        Safely execute Python for:
        - Statistical analysis
        - Custom aggregations
        - Complex calculations
        """
```

## What We DON'T Build

1. **Hardcoded analysis methods**: No `find_underperforming(threshold)`
2. **Fixed thresholds**: LLM decides all criteria
3. **Mock implementations**: Real data only
4. **Unnecessary complexity**: Minimal code

## Capability Registry

Capabilities self-register for discovery:

```python
class CapabilityRegistry:
    """Central registry for all capabilities"""
    
    def __init__(self):
        self.capabilities: Dict[str, BaseCapability] = {}
    
    def register(self, name: str, capability: BaseCapability):
        """Register a capability"""
        self.capabilities[name] = capability
    
    def get(self, name: str) -> BaseCapability:
        """Get capability by name"""
        return self.capabilities.get(name)
    
    def get_all(self) -> List[BaseCapability]:
        """Get all registered capabilities"""
        return list(self.capabilities.values())
    
    def describe_all(self) -> List[CapabilityDescription]:
        """Get descriptions for orchestrator"""
        return [cap.describe() for cap in self.capabilities.values()]

# Initialize and register
registry = CapabilityRegistry()
registry.register("chat", ChatCapability())
registry.register("ticketing_data", TicketingDataCapability())
registry.register("event_analysis", EventAnalysisCapability())
# ... etc
```

## Testing with Real Data

```python
async def test_flexible_analysis():
    """Test with real shows from our database"""
    result = await capability.analyze({
        "query": "Which shows need attention?",
        "entities": ["Gatsby", "Hell's Kitchen", "Outsiders"],
        "criteria": "LLM will decide what 'needs attention' means"
    })
    assert result.success
    assert result.data is not None
```