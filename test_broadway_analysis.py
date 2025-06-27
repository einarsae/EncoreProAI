#!/usr/bin/env python3
"""
Broadway Revenue Analysis Test
Test complete pipeline from Cube.js data to LLM analysis
"""

import asyncio
import time
import logging
from capabilities.ticketing_data import TicketingDataCapability
from capabilities.event_analysis import EventAnalysisCapability
from models.capabilities import (
    TicketingDataInputs, EventAnalysisInputs, 
    AnalysisCriteria, CubeFilter
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_broadway_analysis_pipeline():
    """Test complete pipeline from Cube.js data to LLM analysis"""
    
    start_time = time.time()
    print("🎯 BROADWAY REVENUE ANALYSIS")
    print("=" * 60)
    print(f"Query: 'Analyze revenue performance as of {time.strftime('%B %d, %Y')}'")
    print("Pipeline: Cube.js → EventAnalysisCapability")
    print(f"Context: Data snapshot, not annual totals")
    print("=" * 60)
    
    # Step 1: Get data from Cube.js
    print("\n🔄 Step 1: Fetching data from Cube.js...")
    data_capability = TicketingDataCapability()
    
    data_inputs = TicketingDataInputs(
        session_id="real_data_test",
        tenant_id="5465f607-b975-4c80-bed1-a1a5a3c779e2",  # From .env
        user_id="real_user",
        measures=["ticket_line_items.amount", "ticket_line_items.quantity"],
        dimensions=["productions.name"],  # Correct field from schema!
        filters=[],
        limit=10
    )
    
    data_start = time.time()
    data_result = await data_capability.execute(data_inputs)
    data_time = time.time() - data_start
    
    if not data_result.success:
        print("❌ FAILED to get data from Cube.js")
        print(f"Error: {data_result}")
        return
    
    print(f"✅ Got data in {data_time:.2f}s")
    print(f"   📊 Rows: {data_result.total_rows}")
    print(f"   🎭 Shows: {len(set(dp.dimensions.get('show_name', 'Unknown') for dp in data_result.data))}")
    
    if data_result.total_rows == 0:
        print("⚠️  No data returned - check Cube.js connection and data")
        return
    
    # Show a sample of the data
    print(f"\n📋 Sample data (first 3 rows):")
    for i, dp in enumerate(data_result.data[:3]):
        show = dp.dimensions.get('show_name', 'Unknown')
        amount = dp.measures.get('amount', 0)
        quantity = dp.measures.get('quantity', 0)
        print(f"   {i+1}. {show}: ${amount:,.2f} ({quantity:,} tickets)")
    
    # Step 2: Analyze data with LLM
    print(f"\n🧠 Step 2: Analyzing data with LLM...")
    analysis_capability = EventAnalysisCapability()
    
    # Convert data to analysis format
    analysis_data = {
        "cube_data": {
            "data": [
                {
                    "dimensions": dp.dimensions,
                    "measures": dp.measures
                } for dp in data_result.data
            ],
            "total_rows": data_result.total_rows,
            "query_metadata": data_result.query_metadata,
            "assumptions": data_result.assumptions
        }
    }
    
    analysis_inputs = EventAnalysisInputs(
        session_id="real_analysis",
        tenant_id="5465f607-b975-4c80-bed1-a1a5a3c779e2",
        user_id="real_user",
        data_context=analysis_data,
        analysis_criteria=AnalysisCriteria(
            analysis_type="performance",
            criteria={
                "description": f"Analyze our Broadway revenue performance as of {time.strftime('%B %d, %Y')}. Focus on what this data shows, not annual projections.",
                "focus": "revenue analysis of current Broadway data snapshot",
                "temporal_context": f"Analysis date: {time.strftime('%Y-%m-%d')}",
                "data_scope": "Current data snapshot from Cube.js - not full year totals"
            }
        )
    )
    
    analysis_start = time.time()
    analysis_result = await analysis_capability.execute(analysis_inputs)
    analysis_time = time.time() - analysis_start
    
    total_time = time.time() - start_time
    
    # Display results
    print("=" * 60)
    print("🎯 BROADWAY ANALYSIS RESULTS")
    print("=" * 60)
    
    print(f"\n✅ **Success:** {analysis_result.success}")
    print(f"🎯 **Confidence:** {analysis_result.confidence}")
    
    print(f"\n📋 **Broadway Analysis:**")
    print(f"   {analysis_result.summary}")
    
    print(f"\n🔍 **Key Insights:** ({len(analysis_result.insights)} found)")
    for i, insight in enumerate(analysis_result.insights, 1):
        print(f"   {i}. **{insight.type.title()}** (confidence: {insight.confidence})")
        print(f"      {insight.description}")
    
    print(f"\n💡 **Recommendations:**")
    for i, rec in enumerate(analysis_result.recommendations, 1):
        print(f"   {i}. {rec}")
    
    # Performance metrics
    print(f"\n⚡ **Performance:**")
    print(f"   🔗 Cube.js Query Time: {data_time:.2f}s")
    print(f"   🧠 LLM Analysis Time: {analysis_time:.2f}s")
    print(f"   🚀 Total Pipeline Time: {total_time:.2f}s")
    print(f"   📊 Data Points: {data_result.total_rows}")
    print(f"   🎭 Shows Analyzed: {len(set(dp.dimensions.get('show_name', 'Unknown') for dp in data_result.data))}")
    
    print("\n" + "=" * 60)
    print("🎉 ANALYSIS PIPELINE COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_broadway_analysis_pipeline())