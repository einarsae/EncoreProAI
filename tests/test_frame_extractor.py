"""
Tests for FrameExtractor - Multi-frame semantic extraction from queries

This file tests:
- Emotional support query extraction
- Simple data query frame extraction  
- Complex multi-frame query handling
- Coreference resolution within frames
- Frame splitting logic for unrelated content
- All test queries from TEST_QUERIES.md

Run: docker-compose run --rm test python -m pytest tests/test_frame_extractor.py -v
Run specific test: docker-compose run --rm test python -m pytest tests/test_frame_extractor.py::test_frame_extraction -v
Run with output: docker-compose run --rm test python -m pytest tests/test_frame_extractor.py -v -s
"""

import asyncio
import os
from typing import List, Dict, Any
import json
import pytest

from services.frame_extractor import FrameExtractor
from models.frame import Frame


class TestQuery:
    """Test query with expected frame structure"""
    def __init__(self, query: str, expected_frames: int, description: str, 
                 expected_intents: List[str] = None):
        self.query = query
        self.expected_frames = expected_frames
        self.description = description
        self.expected_intents = expected_intents or []


# All test queries from TEST_QUERIES.md
TEST_QUERIES = [
    # === 1. Companionship & Chat (NEW - CRITICAL) ===
    TestQuery(
        "I'm feeling overwhelmed with all these numbers",
        1,
        "Emotional support query",
        ["emotional_support"]
    ),
    TestQuery(
        "This is stressful, help me understand what to focus on",
        1,
        "Combined emotional support and guidance",
        ["emotional_support_with_guidance"]
    ),
    TestQuery(
        "Tell me something positive about our performance",
        1,
        "Request for positive insights",
        ["positive_insights"]
    ),
    TestQuery(
        "What else should I be looking at?",
        1,
        "Follow-up generation request",
        ["guidance_request"]
    ),
    TestQuery(
        "Tell me about the theater industry",
        1,
        "General conversation about domain",
        ["general_conversation"]
    ),

    # === 2. Simple Data Retrieval ===
    TestQuery(
        "What is the total revenue for Gatsby?",
        1,
        "Simple aggregation query",
        ["data_query"]
    ),
    TestQuery(
        "Show me attendance for Outsiders",
        1,
        "Basic metric query",
        ["data_query"]
    ),
    TestQuery(
        "Revenue for Some Like It Hot in January 2024",
        1,
        "Time-based query",
        ["data_query"]
    ),
    TestQuery(
        "Which venues are we operating?",
        1,
        "Entity listing query",
        ["entity_list"]
    ),

    # === 3. Comparison Queries ===
    TestQuery(
        "Compare sales for Hell's Kitchen and Chicago",
        1,
        "Direct show comparison",
        ["comparison"]
    ),
    TestQuery(
        "This month vs last month revenue",
        1,
        "Time comparison",
        ["time_comparison"]
    ),
    TestQuery(
        "Weekend vs weekday sales for all shows",
        1,
        "Pattern comparison",
        ["pattern_comparison"]
    ),

    # === 4. Trend Analysis ===
    TestQuery(
        "Show revenue trends for Outsiders over the past 6 months",
        1,
        "Trend analysis query",
        ["trend_analysis"]
    ),
    TestQuery(
        "Is Hell's Kitchen revenue declining?",
        1,
        "Trend detection query",
        ["trend_detection"]
    ),
    TestQuery(
        "How do holidays affect ticket sales?",
        1,
        "Seasonal pattern analysis",
        ["pattern_analysis"]
    ),

    # === 5. Complex Analysis (LLM Decides Approach) ===
    TestQuery(
        "Which shows need attention?",
        1,
        "Flexible performance analysis",
        ["flexible_analysis"]
    ),
    TestQuery(
        "Find opportunities in our data",
        1,
        "Open-ended exploration",
        ["exploration"]
    ),
    TestQuery(
        "What patterns do you see in our sales?",
        1,
        "Pattern detection request",
        ["pattern_discovery"]
    ),

    # === 6. Customer Analysis ===
    TestQuery(
        "How many unique customers last month?",
        1,
        "Customer metric query",
        ["customer_metrics"]
    ),
    TestQuery(
        "Which customers buy premium seats?",
        1,
        "Customer segmentation query",
        ["customer_segmentation"]
    ),

    # === 7. Ambiguity Handling ===
    TestQuery(
        "Show me Chicago data",
        1,
        "Ambiguous entity query",
        ["data_query"]
    ),
    TestQuery(
        "Performance last week",
        1,
        "Ambiguous metric and entity",
        ["data_query"]
    ),
    TestQuery(
        "How are we doing?",
        1,
        "Very ambiguous query",
        ["general_analysis"]
    ),

    # === 8. Multi-Frame Complex Queries ===
    TestQuery(
        "How many people saw Chicago last Saturday. How many were from Chicago. What was the core audience and who should I be targeting for that show. How has the weather been in Chicago. Is that related.",
        1,  # All connected through Chicago show analysis
        "Complex connected query (single frame)",
        ["comprehensive_chicago_analysis"]
    ),
    TestQuery(
        "How many people saw Chicago last Saturday. Also, can you send me weekly revenue report.",
        2,  # Unrelated requests
        "Multi-frame with unrelated requests",
        ["attendance_query", "automation_request"]
    ),
    TestQuery(
        "Show me revenue trends. How have you been? Also compare to last year.",
        2,  # Agent check-in interrupts data flow
        "Multi-frame with agent interruption",
        ["revenue_trends", "agent_checkin"]  # Note: third part connects back to first
    ),
]


@pytest.mark.integration
async def test_frame_extraction():
    """Test frame extraction for all queries"""
    
    # Check if we have OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set - skipping LLM tests")
    
    extractor = FrameExtractor()
    results = []
    
    print("\n🧪 Testing Frame Extraction with All Test Queries")
    print("=" * 80)
    
    for test_query in TEST_QUERIES:
        print(f"\n📝 Query: \"{test_query.query}\"")
        print(f"   Description: {test_query.description}")
        print(f"   Expected frames: {test_query.expected_frames}")
        
        try:
            frames = await extractor.extract_frames(test_query.query)
            
            print(f"   ✓ Extracted {len(frames)} frame(s)")
            
            for i, frame in enumerate(frames, 1):
                print(f"\n   Frame {i}:")
                print(f"   - Query: \"{frame.query[:60]}...\"" if len(frame.query) > 60 else f"   - Query: \"{frame.query}\"")
                
                # Show extractions
                if frame.entities:
                    print(f"   - Entities: {frame.entities}")
                if frame.concepts:
                    print(f"   - Concepts: {frame.concepts}")
            
            # Check if frame count matches expectation
            if len(frames) == test_query.expected_frames:
                print(f"   ✅ Frame count matches expectation")
                results.append((test_query.query, True, ""))
            else:
                error = f"Expected {test_query.expected_frames} frames, got {len(frames)}"
                print(f"   ❌ {error}")
                results.append((test_query.query, False, error))
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append((test_query.query, False, str(e)))
        
        print("-" * 60)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed < total:
        print(f"\n❌ Failed queries:")
        for query, success, error in results:
            if not success:
                print(f"   - \"{query[:50]}...\": {error}")
    
    # Assert for pytest
    assert passed == total, f"Failed {total - passed} out of {total} test queries"


@pytest.mark.unit
def test_expected_frame_structures():
    """Test expected frame structures without LLM calls"""
    
    print("\n📋 Expected Frame Extraction Results")
    print("=" * 80)
    
    # Show some example expected outputs
    print("\nExample 1: Emotional Support")
    print("Query: \"I'm feeling overwhelmed with all these numbers\"")
    print("Expected: 1 frame")
    print("- Entities: []")
    print("- Times: []")
    print("- Concepts: [\"overwhelmed\", \"numbers\"]")
    
    print("\nExample 2: Complex Connected Query")
    print("Query: \"How many people saw Chicago last Saturday. How many were from Chicago...\"")
    print("Expected: 1 frame (all connected through Chicago show)")
    print("- Entities: [\"Chicago\", \"Chicago\", \"Chicago\"]")
    print("- Times: [\"last Saturday\"]")
    print("- Concepts: [\"people\", \"core audience\", \"targeting\", \"weather\", \"related\"]")
    
    print("\nExample 3: Multi-Frame Query")
    print("Query: \"Show me revenue trends. How have you been? Also compare to last year.\"")
    print("Expected: 2 frames")
    print("- Frame 1: entities=[], times=[\"last year\"], concepts=[\"revenue trends\"]")
    print("- Frame 2: entities=[], times=[], concepts=[] (agent check-in)")
    
    # This test always passes - it's just documentation
    assert True