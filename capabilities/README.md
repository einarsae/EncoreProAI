# Capabilities

This directory contains the business logic capabilities that power EncoreProAI.

## Implemented Capabilities

### ✅ ChatCapability (`chat.py`)
- **Purpose**: Empathetic AI companion for theater professionals
- **Features**:
  - Emotional support detection and response
  - Concise, contextual responses (2-3 sentences)
  - Industry-specific language (theater, Broadway, touring)
  - User context awareness (role, organization)
  - Preference update suggestions every 10 messages
  - Follow-up question generation
- **Models**: 
  - Primary: Claude Sonnet 4 (via Anthropic)
  - Fallback: GPT-4 (via OpenAI)

## TODO: LangGraph/LangChain Integration

To make model switching easier and support multiple providers:

1. **Install dependencies**:
   ```bash
   pip install langchain langchain-anthropic langchain-openai
   ```

2. **Update ChatCapability** to use LangChain:
   ```python
   from langchain_anthropic import ChatAnthropic
   from langchain_openai import ChatOpenAI
   from langchain.schema import HumanMessage, SystemMessage
   
   # Easy model switching
   self.llm = ChatAnthropic(model="claude-sonnet-4-20250514")
   # or
   self.llm = ChatOpenAI(model="gpt-4o-mini")
   ```

3. **Benefits**:
   - Unified interface for all LLMs
   - Easy provider switching
   - Built-in retry logic
   - Streaming support
   - LangSmith tracing (already configured in .env)

## Upcoming Capabilities

- **TicketingDataCapability**: Cube.js data access
- **EventAnalysisCapability**: LLM-driven analysis
- **MemoryCapability**: Vector memory with pgvector

## Key Design Principles

1. **No Mocks**: All capabilities use real services
2. **Typed I/O**: Pydantic models for validation
3. **Self-Contained**: Each capability is independent
4. **LLM-Driven**: No hardcoded thresholds or rules
5. **Context-Aware**: Use user/industry context