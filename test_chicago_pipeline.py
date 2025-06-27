#!/usr/bin/env python3
"""
Test Chicago Pipeline - Full orchestration test
"""

import asyncio
import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow.graph import process_query

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_chicago_pipeline():
    """Test the full Chicago orchestration pipeline"""
    
    print("🏙️  CHICAGO PERFORMANCE ANALYSIS PIPELINE")
    print("=" * 60)
    print("Query: 'I'm worried about Chicago. How is it performing?'")
    print("Testing: Frame extraction → Entity resolution → Orchestration")
    print("=" * 60)
    
    try:
        result = await process_query(
            query="I'm worried about Chicago. How is it performing?",
            session_id="chicago_pipeline_test",
            user_id="test_user", 
            tenant_id="5465f607-b975-4c80-bed1-a1a5a3c779e2",
            debug=True
        )
        
        print("\n🎯 PIPELINE RESULTS")
        print("=" * 40)
        print(f"✅ Success: {result['success']}")
        
        if result['success']:
            print(f"📋 Response Type: {type(result.get('response', 'None'))}")
            print(f"🎭 Final Response: {result.get('response', 'No response')}")
            
            # Show message history if available
            if result.get('messages'):
                print(f"\n💬 Message History ({len(result['messages'])} messages):")
                for i, msg in enumerate(result['messages'][-5:], 1):  # Last 5 messages
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:100]  # First 100 chars
                    print(f"   {i}. [{role}]: {content}...")
            
            # Show debug info if available
            if result.get('debug'):
                print(f"\n🔍 Debug Events: {len(result['debug'].get('trace_events', []))}")
                for event in result['debug'].get('trace_events', [])[-5:]:
                    print(f"   - {event.get('event_type', 'unknown')}: {event.get('data', {})}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Pipeline failed with exception: {e}")
        logger.exception("Chicago pipeline test failed")
        return False
    
    print("\n" + "=" * 60)
    print("🏁 CHICAGO PIPELINE TEST COMPLETED")
    print("=" * 60)
    return result['success']

if __name__ == "__main__":
    asyncio.run(test_chicago_pipeline())