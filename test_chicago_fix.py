"""
Test Chicago pipeline and verify proper data extraction in response
"""

import asyncio
import os
import json
from datetime import datetime

from workflow.graph import process_query


async def test_queries():
    """Test various revenue queries"""
    
    queries = [
        "What is the total revenue for Chicago?",
        "What is the total revenue for Gatsby?", 
        "Show me revenue data",
        "How much money did we make?"
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        result = await process_query(
            query=query,
            session_id=f"test_{query[:10]}",
            user_id="user123",
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
            debug=False
        )
        
        print(f"\nSuccess: {result.get('success')}")
        
        if result.get('response'):
            response = result['response']
            print(f"\nResponse message: {response.get('message')}")
            print(f"Confidence: {response.get('confidence')}")
            print(f"Data source: {response.get('data_source')}")
            
        if result.get('error'):
            print(f"Error: {result['error']}")


async def test_broadway_shows():
    """Test with actual Broadway show names"""
    
    shows = ["Hamilton", "The Lion King", "Chicago", "Wicked", "The Book of Mormon"]
    
    for show in shows:
        print(f"\n{'='*60}")
        print(f"Testing: {show}")
        print('='*60)
        
        result = await process_query(
            query=f"What is the total revenue for {show}?",
            session_id=f"test_{show}",
            user_id="user123", 
            tenant_id=os.getenv("DEFAULT_TENANT_ID", "5465f607-b975-4c80-bed1-a1a5a3c779e2"),
            debug=False
        )
        
        if result.get('success') and result.get('response'):
            print(f"Response: {result['response']['message']}")
        else:
            print(f"Failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    print("Testing various revenue queries...")
    asyncio.run(test_queries())
    
    print("\n\n" + "="*80)
    print("Testing specific Broadway shows...")
    print("="*80)
    asyncio.run(test_broadway_shows())