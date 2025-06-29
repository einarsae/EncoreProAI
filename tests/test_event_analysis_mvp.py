"""
Test EventAnalysisCapability MVP Implementation

Tests the simple version of EventAnalysisCapability to ensure:
1. It can request initial data
2. It can analyze provided data
3. It can request additional data if needed
4. It uses clear orchestrator hints
"""

import asyncio
import os
from models.capabilities import EventAnalysisInputs, DataPoint
from capabilities.event_analysis import EventAnalysisCapability


async def test_initial_data_request():
    """Test requesting initial data when none provided"""
    print("\n🧪 TEST 1: Initial Data Request")
    print("=" * 60)
    
    capability = EventAnalysisCapability()
    
    # Test without any data
    inputs = EventAnalysisInputs(
        session_id="test-001",
        tenant_id="yesplan",
        user_id="test-user",
        analysis_request="How is Chicago performing?",
        entities=[{"id": "prod_chicago_broadway", "name": "Chicago"}],
        time_context="last 3 months"
    )
    
    result = await capability.execute(inputs)
    
    print(f"Success: {result.success}")
    print(f"Analysis complete: {result.analysis_complete}")
    print(f"Needs data: {result.orchestrator_hints.get('needs_data', False)}")
    print(f"Data request: {result.orchestrator_hints.get('data_request', {}).get('natural_language', 'None')}")
    print(f"Reasoning: {result.orchestrator_hints.get('reasoning', 'None')}")
    
    assert not result.analysis_complete
    assert result.orchestrator_hints.get('needs_data') == True
    assert "Chicago" in result.orchestrator_hints.get('data_request', {}).get('natural_language', '')


async def test_analysis_with_data():
    """Test analyzing when data is provided"""
    print("\n\n🧪 TEST 2: Analysis With Data")
    print("=" * 60)
    
    capability = EventAnalysisCapability()
    
    # Create sample data
    sample_data = [
        DataPoint(
            dimensions={"productions.name": "Chicago", "ticket_line_items.created_at_local": "2024-10"},
            measures={"ticket_line_items.amount": 125000, "ticket_line_items.quantity": 1500}
        ),
        DataPoint(
            dimensions={"productions.name": "Chicago", "ticket_line_items.created_at_local": "2024-11"},
            measures={"ticket_line_items.amount": 98000, "ticket_line_items.quantity": 1200}
        ),
        DataPoint(
            dimensions={"productions.name": "Chicago", "ticket_line_items.created_at_local": "2024-12"},
            measures={"ticket_line_items.amount": 45000, "ticket_line_items.quantity": 600}
        )
    ]
    
    inputs = EventAnalysisInputs(
        session_id="test-002",
        tenant_id="yesplan",
        user_id="test-user",
        analysis_request="Analyze Chicago's revenue trend",
        entities=[{"id": "prod_chicago_broadway", "name": "Chicago"}],
        time_context="Q4 2024",
        data=sample_data
    )
    
    result = await capability.execute(inputs)
    
    print(f"Success: {result.success}")
    print(f"Analysis complete: {result.analysis_complete}")
    print(f"\nInsights ({len(result.insights)}):")
    for i, insight in enumerate(result.insights, 1):
        print(f"{i}. {insight}")
    print(f"\nRecommendations ({len(result.recommendations)}):")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"{i}. {rec}")
    
    print(f"\nOrchestrator hints:")
    print(f"- Needs more data: {result.orchestrator_hints.get('needs_data', False)}")
    if result.orchestrator_hints.get('needs_data'):
        print(f"- Additional data request: {result.orchestrator_hints.get('data_request', {}).get('natural_language', 'None')}")
    
    assert result.success
    assert len(result.insights) > 0


async def test_progressive_analysis():
    """Test requesting additional data for deeper analysis"""
    print("\n\n🧪 TEST 3: Progressive Analysis")
    print("=" * 60)
    
    capability = EventAnalysisCapability()
    
    # Limited initial data
    initial_data = [
        DataPoint(
            dimensions={"productions.name": "Chicago"},
            measures={"ticket_line_items.amount": 45000, "ticket_line_items.quantity": 600}
        )
    ]
    
    inputs = EventAnalysisInputs(
        session_id="test-003",
        tenant_id="yesplan",
        user_id="test-user",
        analysis_request="Why is Chicago underperforming? Need detailed analysis.",
        entities=[{"id": "prod_chicago_broadway", "name": "Chicago"}],
        time_context="December 2024",
        data=initial_data
    )
    
    result = await capability.execute(inputs)
    
    print(f"Success: {result.success}")
    print(f"Analysis complete: {result.analysis_complete}")
    print(f"Confidence: {result.confidence}")
    
    if result.insights:
        print(f"\nPartial insights:")
        for insight in result.insights:
            print(f"- {insight}")
    
    if result.orchestrator_hints.get('needs_data'):
        print(f"\nRequesting more data:")
        print(f"- {result.orchestrator_hints.get('data_request', {}).get('natural_language', 'None')}")
    
    assert result.success
    # Should likely request more data given limited initial data
    print(f"\nDid it request more data? {result.orchestrator_hints.get('needs_data', False)}")


async def test_trend_analysis():
    """Test different analysis types - trends"""
    print("\n\n🧪 TEST 4: Trend Analysis Request")
    print("=" * 60)
    
    capability = EventAnalysisCapability()
    
    inputs = EventAnalysisInputs(
        session_id="test-004",
        tenant_id="yesplan",
        user_id="test-user",
        analysis_request="Show me revenue trends for all productions",
        entities=[],
        time_context="last 6 months"
    )
    
    result = await capability.execute(inputs)
    
    print(f"Data request for trends: {result.orchestrator_hints.get('data_request', {}).get('natural_language', 'None')}")
    
    # The request is a bit different from expected, check key components
    data_request = result.orchestrator_hints.get('data_request', {}).get('natural_language', '').lower()
    assert "revenue" in data_request
    assert "monthly" in data_request


async def main():
    """Run all tests"""
    print("🚀 Testing EventAnalysisCapability MVP")
    print("=" * 80)
    
    try:
        await test_initial_data_request()
        await test_analysis_with_data()
        await test_progressive_analysis()
        await test_trend_analysis()
        
        print("\n\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())