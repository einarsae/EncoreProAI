#!/usr/bin/env python3
"""
Test all queries from TEST_QUERIES.md with real data
"""

import asyncio
import os
import logging
from workflow.graph import create_workflow
from models.state import AgentState

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


async def test_query(query: str, session_id: str = "test_session"):
    """Test a single query"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing: {query}")
    logger.info(f"{'='*60}")
    
    try:
        # Create workflow
        app = create_workflow()
        
        # Create initial state
        initial_state = AgentState(
            core={
                "session_id": session_id,
                "user_id": "test_user",
                "tenant_id": os.getenv("TENANT_ID", "yesplan"),
                "query": query
            }
        )
        
        # Track execution
        steps = []
        final_response = None
        
        # Run workflow
        async for event in app.astream(initial_state):
            for node, state in event.items():
                step_info = {"node": node}
                
                # Capture key information
                if hasattr(state, 'routing') and state.routing.next_node:
                    step_info["next"] = state.routing.next_node
                    if state.routing.capability_to_execute:
                        step_info["capability"] = state.routing.capability_to_execute
                
                if hasattr(state, 'execution'):
                    step_info["tasks"] = list(state.execution.completed_tasks.keys())
                    step_info["loop"] = state.execution.loop_count
                
                if hasattr(state, 'core') and state.core.final_response:
                    final_response = state.core.final_response
                
                steps.append(step_info)
                logger.info(f"Step {len(steps)}: {step_info}")
        
        # Check results
        success = final_response is not None
        
        logger.info(f"\nResult: {'✅ SUCCESS' if success else '❌ FAILED'}")
        if final_response:
            if hasattr(final_response, 'message'):
                logger.info(f"Response: {final_response.message}")
            else:
                logger.info(f"Response: {final_response}")
        logger.info(f"Total steps: {len(steps)}")
        
        return {
            "query": query,
            "success": success,
            "steps": len(steps),
            "response": final_response,
            "execution_path": steps
        }
        
    except Exception as e:
        logger.error(f"Error testing query: {e}")
        return {
            "query": query,
            "success": False,
            "error": str(e)
        }


async def test_category(category_name: str, queries: list):
    """Test a category of queries"""
    logger.info(f"\n{'#'*80}")
    logger.info(f"Testing Category: {category_name.upper()}")
    logger.info(f"{'#'*80}")
    
    results = []
    for query in queries:
        result = await test_query(query)
        results.append(result)
        await asyncio.sleep(1)  # Rate limiting
    
    # Summary
    successful = sum(1 for r in results if r.get("success"))
    logger.info(f"\nCategory Summary: {successful}/{len(queries)} successful")
    
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