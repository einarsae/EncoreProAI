#!/usr/bin/env python3
"""
Test all queries from TEST_QUERIES.md with real data
"""

import asyncio
import os
import logging
import warnings
from workflow.graph import create_workflow
from models.state import AgentState

# Suppress Pydantic deprecation warnings from LangGraph
warnings.filterwarnings("ignore", message=".*model_fields.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*PydanticDeprecatedSince211.*")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Test queries organized by category
TEST_QUERIES = {
    "simple_data": [
        "What is the total revenue for Gatsby?",
        "How many tickets were sold for Hell's Kitchen?",
        "Show me attendance for Outsiders",
        "What is the average ticket price for Chicago?",
        "Total revenue across all shows"
    ],
    "time_based": [
        "Revenue for Some Like It Hot in January 2024",
        "Show me last week's ticket sales",
        "How many tickets sold yesterday?",
        "What were last month's sales?"
    ],
    "comparisons": [
        "Compare sales for Hell's Kitchen and Chicago",
        "Gatsby vs Outsiders revenue last quarter",
        "Which show performed better: Hell's Kitchen or Some Like It Hot?",
        "Compare all shows by attendance"
    ],
    "trends": [
        "Show revenue trends for Outsiders over the past 6 months",
        "How has attendance changed for Chicago since opening?",
        "Monthly ticket sales trend for all productions",
        "Is Hell's Kitchen revenue declining?"
    ],
    "analysis": [
        "Which shows need attention?",
        "Find opportunities in our data",
        "What's interesting about Gatsby's performance?",
        "How are our shows doing?"
    ],
    "emotional_support": [
        "I'm feeling overwhelmed with all these numbers",
        "This is stressful, help me understand what to focus on",
        "I don't know where to start with analyzing my shows",
        "Tell me something positive about our performance"
    ],
    "ambiguous": [
        "Show me Chicago data",
        "Performance last week",
        "Compare our best shows",
        "How are we doing?"
    ]
}


async def test_query(query: str, session_id: str = "test_session", timeout: int = 120):
    """Test a single query with timeout"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing: {query}")
    logger.info(f"{'='*60}")
    
    try:
        # Add timeout to prevent hanging
        result = await asyncio.wait_for(
            process_query(
                query=query,
                session_id=session_id,
                user_id="test_user",
                tenant_id=os.getenv("TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
                debug=False
            ),
            timeout=timeout
        )
        
        # Check results
        success = result.get("success", False)
        error = result.get("error")
        response = result.get("response")
        
        logger.info(f"\nResult: {'✅ SUCCESS' if success else '❌ FAILED'}")
        if error:
            logger.info(f"Error: {error}")
        if response:
            if isinstance(response, dict) and "message" in response:
                logger.info(f"Response: {response['message'][:200]}...")
            else:
                logger.info(f"Response: {response}")
        
        return {
            "query": query,
            "success": success,
            "response": response,
            "error": error
        }
        
    except asyncio.TimeoutError:
        logger.error(f"❌ TIMEOUT: Query took longer than {timeout} seconds")
        return {
            "query": query,
            "success": False,
            "error": f"Timeout after {timeout} seconds"
        }
        
    except Exception as e:
        logger.error(f"Error testing query: {e}")
        return {
            "query": query,
            "success": False,
            "error": str(e)
        }

# Add missing import
from workflow.graph import process_query


async def test_category(category_name: str, queries: list, max_queries: int = 3):
    """Test a category of queries (limited for performance)"""
    logger.info(f"\n{'#'*80}")
    logger.info(f"Testing Category: {category_name.upper()}")
    logger.info(f"{'#'*80}")
    
    # Limit queries for faster testing
    test_queries = queries[:max_queries]
    if len(queries) > max_queries:
        logger.info(f"Testing first {max_queries} of {len(queries)} queries for performance")
    
    results = []
    for query in test_queries:
        result = await test_query(query, timeout=120)  # Increased timeout for API delays
        results.append(result)
        await asyncio.sleep(2)  # Slightly longer delay
    
    # Summary
    successful = sum(1 for r in results if r.get("success"))
    logger.info(f"\nCategory Summary: {successful}/{len(test_queries)} successful")
    
    return results


async def test_all_queries():
    """Test all query categories"""
    logger.info("Starting comprehensive query testing...")
    
    all_results = {}
    
    # Test each category
    for category, queries in TEST_QUERIES.items():
        results = await test_category(category, queries)
        all_results[category] = results
    
    # Overall summary
    logger.info(f"\n{'='*80}")
    logger.info("OVERALL SUMMARY")
    logger.info(f"{'='*80}")
    
    total_queries = 0
    total_successful = 0
    
    for category, results in all_results.items():
        successful = sum(1 for r in results if r.get("success"))
        total = len(results)
        total_queries += total
        total_successful += successful
        
        logger.info(f"{category:20} {successful:3d}/{total:3d} ({successful/total*100:.0f}%)")
    
    logger.info(f"\n{'TOTAL':20} {total_successful:3d}/{total_queries:3d} ({total_successful/total_queries*100:.0f}%)")
    
    # Show failures
    failures = []
    for category, results in all_results.items():
        for result in results:
            if not result.get("success"):
                failures.append((category, result))
    
    if failures:
        logger.info(f"\n{'='*80}")
        logger.info("FAILURES")
        logger.info(f"{'='*80}")
        for category, result in failures:
            logger.info(f"\n[{category}] {result['query']}")
            if "error" in result:
                logger.info(f"Error: {result['error']}")
    
    return all_results


async def test_multi_turn():
    """Test multi-turn conversation"""
    logger.info(f"\n{'#'*80}")
    logger.info("Testing Multi-Turn Conversation")
    logger.info(f"{'#'*80}")
    
    session_id = "multi_turn_test"
    
    queries = [
        "Show me Gatsby revenue",
        "How about last month?",
        "Compare to Hell's Kitchen",
        "What drives the difference?"
    ]
    
    for i, query in enumerate(queries):
        logger.info(f"\nTurn {i+1}: {query}")
        result = await test_query(query, session_id)
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(test_all_queries())
    # Optionally test multi-turn
    # asyncio.run(test_multi_turn())