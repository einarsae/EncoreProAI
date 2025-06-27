"""
Multi-Frame Extraction Service - Break queries into semantically complete units

Each frame is a semantically complete unit that can be processed independently.
Everything related or part of the same context stays together in one frame.
"""

import asyncio
import os
import json
from typing import List, Dict, Any, Optional
import httpx

from models.frame import Frame, EntityToResolve


class FrameExtractor:
    """Extract semantically complete frames from user queries"""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required for frame extraction")
        # Use standard tier by default for frame extraction
        self.model = model or os.getenv("LLM_TIER_STANDARD", "gpt-4.1-mini-2025-04-14")
    
    async def extract_frames(self, query: str, context: Dict[str, Any] = None) -> List[Frame]:
        """Extract one or more semantically complete frames"""
        
        prompt = self._build_extraction_prompt(query, context or {})
        response = await self._call_openai(prompt)
        frames = self._parse_response(response, query)
        
        return frames
    
    def _build_extraction_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Build prompt for semantic frame extraction"""

        context_str = ""
        if context.get("previous_entities"):
            context_str = f"\nRecent context: {context['previous_entities']}"

        return f"""
You are a semantic interpreter specializing in live entertainment audience development, marketing, segmentation, strategy, reporting and automation.
Your task is to extract what needs resolution from user queries.

---

### 1. What to Extract

From each semantic unit, extract ONLY:
- **Entities**: Things that need database lookup with their guessed type:
  - productions: Shows, musicals, plays (e.g., "Chicago", "Gatsby", "Hamilton")
  - venues: Theater locations (e.g., specific theater names)
  - performers: Actors, artists (currently empty in our data)
  - cities: Geographic locations (e.g., "New York", "Chicago" the city)
  - states: US states (e.g., "New York", "California")
  - countries: Country names
  - retailers: Ticket sellers (e.g., specific retailer names)
  - payment_methods: Payment types
  - price_bands: Ticket price categories
  - seating_plans: Seating configurations
  - ticket_types: Types of tickets
  - sales_channels: How tickets are sold
- **Concepts**: Any concepts that might benefit from memory context (metrics, emotions, strategies, actions, analysis, automation, segmentation) - NOT time expressions

---

### 2. When to Split into Multiple Frames

Create a new Frame ONLY when concepts are truly independent and cannot be answered together.
Keep all coreferences, related questions, and connected context in the SAME frame.

Split only when:
* Non of the created frames loose context or information from the original query by standing alone
* Agent-directed conversation interrupting data queries ("how have you been?")
* Different semantic domains that share no entities or concepts

Example 1 - Single Frame (connected):
Query: "How many people saw Chicago last Saturday. How many were from Chicago. What was the core audience and who should I be targeting for that show. How has the weather been in Chicago. Is that related."
Result: One frame with all extractions since everything relates to Chicago show analysis

Example 2 - Multiple Frames (unrelated):
Query: "How many people saw Chicago last Saturday. Also, can you send me weekly revenue report."
Result: Two frames - attendance query and automation request are unrelated

---

### 3. Output Format

Return a JSON array of frames. Each frame must include:

```json
{{
  "id": "f1",
  "query": "The original text for this semantic unit",
  "entities": [
    {{"id": "e1", "text": "Chicago", "type": "production"}},
    {{"id": "e2", "text": "New York", "type": "city"}}
  ],
  "concepts": ["revenue", "attendance", "overwhelmed", "stressed", "pace curves", "compare", "high value customers"]
}}
```

Notes:
- Assign unique IDs: frames (f1, f2...), entities (e1, e2...)
- Guess entity types based on context (production, city, venue, etc.)
- Include emotional words (overwhelmed, frustrated) as concepts
- Include analysis keywords (trends, performance, insights) as concepts
- Include automation keywords (report, send, schedule) as concepts
- Include segmentation keywords (audience, targeting, demographics) as concepts
- Extract each unique entity with its own ID
- Preserve original text exactly as it appears
- If unsure of entity type, use best guess based on context
- DO NOT include time expressions in concepts

Always return valid JSON - no markdown, comments, or extra keys.

---

{context_str}

User Query: "{query}"
"""
    
    async def _call_openai(self, prompt: str) -> List[Dict[str, Any]]:
        """Call OpenAI API for frame extraction"""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Extract semantically complete frames. Each frame must be self-contained. Return only valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                }
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            try:
                parsed = json.loads(content)
                return parsed if isinstance(parsed, list) else [parsed]
            except json.JSONDecodeError as e:
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    # Fallback to single frame
                    return [{"query": content, "entities": [], "times": [], "concepts": []}]
    
    def _parse_response(self, llm_response: List[Dict[str, Any]], original_query: str) -> List[Frame]:
        """Parse LLM response into Frame objects"""
        
        frames = []
        
        for i, frame_data in enumerate(llm_response):
            try:
                # Parse entities with their types
                entities = []
                for entity_data in frame_data.get("entities", []):
                    if isinstance(entity_data, dict):
                        entities.append(EntityToResolve(
                            id=entity_data.get("id", f"e{len(entities)+1}"),
                            text=entity_data.get("text", ""),
                            type=entity_data.get("type", "unknown")
                        ))
                
                frame = Frame(
                    id=frame_data.get("id", f"f{i+1}"),
                    query=frame_data.get("query", ""),
                    entities=entities,
                    concepts=frame_data.get("concepts", [])
                )
                frames.append(frame)
                
            except Exception as e:
                print(f"Error parsing frame {i}: {e}")
                continue
        
        # Fallback if no frames parsed
        if not frames:
            frames.append(Frame(
                id="f1",
                query=original_query,
                entities=[],
                concepts=[]
            ))
        
        return frames
    
    def get_summary(self, frames: List[Frame]) -> str:
        """Get brief summary of extracted frames"""
        
        if not frames:
            return "No frames"
        
        summaries = []
        for i, frame in enumerate(frames, 1):
            entity_count = len(frame.entities)
            concept_count = len(frame.concepts)
            
            summary = f"Frame {i}: {entity_count} entities, {concept_count} concepts"
            summaries.append(summary)
        
        return "; ".join(summaries)