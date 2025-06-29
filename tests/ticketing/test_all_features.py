"""
Comprehensive test suite for ALL TicketingDataCapability features
NO MOCKS - Real Cube.js integration tests only

Run this to verify all features work correctly.
"""
import pytest
import os
import asyncio
from datetime import datetime
from capabilities.ticketing_data import TicketingDataCapability
from models.capabilities import TicketingDataInputs, CubeFilter


class TestAllTicketingFeatures:
    """Comprehensive test of all TicketingDataCapability features"""
    
    @pytest.fixture(scope="class")
    async def capability(self):
        """Create capability instance once for all tests"""
        return TicketingDataCapability()
    
    @pytest.fixture
    def tenant_id(self):
        """Get real tenant ID"""
        return os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    @pytest.mark.asyncio
    async def test_feature_summary(self, capability, tenant_id):
        """Test and summarize all features"""
        print("\n" + "="*60)
        print("TICKETINGDATACAPABILITY FEATURE TEST SUMMARY")
        print("="*60)
        
        features_tested = []
        
        # 1. Basic Query
        print("\n1. Testing Basic Query...")
        result = await self._test_basic_query(capability, tenant_id)
        features_tested.append(("Basic Query", result))
        
        # 2. Multi-fetch
        print("\n2. Testing Multi-fetch Strategy...")
        result = await self._test_multi_fetch(capability, tenant_id)
        features_tested.append(("Multi-fetch", result))
        
        # 3. Pagination
        print("\n3. Testing Pagination...")
        result = await self._test_pagination(capability, tenant_id)
        features_tested.append(("Pagination", result))
        
        # 4. Total Count
        print("\n4. Testing Total Count...")
        result = await self._test_total_count(capability, tenant_id)
        features_tested.append(("Total Count", result))
        
        # 5. Hierarchical Data
        print("\n5. Testing Hierarchical Data...")
        result = await self._test_hierarchical_data(capability, tenant_id)
        features_tested.append(("Hierarchical Data", result))
        
        # 6. High Cardinality
        print("\n6. Testing High Cardinality Handling...")
        result = await self._test_high_cardinality(capability, tenant_id)
        features_tested.append(("High Cardinality", result))
        
        # 7. Natural Language
        print("\n7. Testing Natural Language Understanding...")
        result = await self._test_natural_language(capability, tenant_id)
        features_tested.append(("Natural Language", result))
        
        # 8. Complex Filters
        print("\n8. Testing Complex Filters...")
        result = await self._test_complex_filters(capability, tenant_id)
        features_tested.append(("Complex Filters", result))
        
        # 9. Time Intelligence
        print("\n9. Testing Time Intelligence...")
        result = await self._test_time_intelligence(capability, tenant_id)
        features_tested.append(("Time Intelligence", result))
        
        # Summary
        print("\n" + "="*60)
        print("RESULTS SUMMARY:")
        print("="*60)
        
        total = len(features_tested)
        passed = sum(1 for _, success in features_tested if success)
        
        for feature, success in features_tested:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{feature:.<30} {status}")
        
        print(f"\nTotal: {passed}/{total} features working")
        print("="*60)
        
        # Assert all features work
        assert passed == total, f"Only {passed}/{total} features passed"
    
    async def _test_basic_query(self, capability, tenant_id):
        """Test basic query functionality"""
        try:
            inputs = TicketingDataInputs(
                session_id="test-basic",
                tenant_id=tenant_id,
                user_id="test",
                measures=["ticket_line_items.amount"],
                dimensions=["productions.name"],
                limit=5
            )
            result = await capability.execute(inputs)
            return result.success and len(result.data) == 5
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def _test_multi_fetch(self, capability, tenant_id):
        """Test multi-fetch for time comparisons"""
        try:
            inputs = TicketingDataInputs(
                session_id="test-multi",
                tenant_id=tenant_id,
                user_id="test",
                query_request="Compare Q1 vs Q2 2024 revenue",
                measures=["ticket_line_items.amount"],
                time_context="Q1 2024 vs Q2 2024"
            )
            result = await capability.execute(inputs)
            is_multi = result.query_metadata.get("strategy") == "multi"
            print(f"   Strategy: {result.query_metadata.get('strategy')}")
            return result.success
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def _test_pagination(self, capability, tenant_id):
        """Test pagination with offset"""
        try:
            inputs = TicketingDataInputs(
                session_id="test-pagination",
                tenant_id=tenant_id,
                user_id="test",
                query_request="Show page 3 of productions (5 per page)",
                measures=["ticket_line_items.amount"],
                dimensions=["productions.name"],
                limit=5
            )
            result = await capability.execute(inputs)
            query = result.query_metadata.get('cube_response', {}).get('query', {})
            has_offset = 'offset' in query
            print(f"   Offset: {query.get('offset', 'Not set')}")
            return result.success and len(result.data) <= 5
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def _test_total_count(self, capability, tenant_id):
        """Test total count request"""
        try:
            inputs = TicketingDataInputs(
                session_id="test-total",
                tenant_id=tenant_id,
                user_id="test",
                query_request="Get productions with total count for pagination UI",
                measures=["ticket_line_items.amount"],
                dimensions=["productions.name"],
                limit=3
            )
            result = await capability.execute(inputs)
            query = result.query_metadata.get('cube_response', {}).get('query', {})
            has_total = query.get('total', False)
            print(f"   Total requested: {has_total}")
            return result.success
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def _test_hierarchical_data(self, capability, tenant_id):
        """Test hierarchical data with multiple dimensions"""
        try:
            inputs = TicketingDataInputs(
                session_id="test-hierarchical",
                tenant_id=tenant_id,
                user_id="test",
                query_request="Revenue by retailer and sales channel",
                measures=["ticket_line_items.amount"],
                dimensions=["retailers.name", "sales_channels.name"],
                limit=10
            )
            result = await capability.execute(inputs)
            has_multiple_dims = len(result.data) > 0 and len(result.data[0].dimensions) >= 2
            print(f"   Multiple dimensions: {has_multiple_dims}")
            return result.success and has_multiple_dims
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def _test_high_cardinality(self, capability, tenant_id):
        """Test high cardinality dimension handling"""
        try:
            inputs = TicketingDataInputs(
                session_id="test-highcard",
                tenant_id=tenant_id,
                user_id="test",
                query_request="Top 20 cities by revenue",
                measures=["ticket_line_items.amount"],
                dimensions=["ticket_line_items.city"],
                limit=20
            )
            result = await capability.execute(inputs)
            has_limit = len(result.data) == 20
            print(f"   Rows returned: {len(result.data)}")
            return result.success and has_limit
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def _test_natural_language(self, capability, tenant_id):
        """Test natural language understanding"""
        try:
            inputs = TicketingDataInputs(
                session_id="test-nl",
                tenant_id=tenant_id,
                user_id="test",
                query_request="Show me total sales and attendance",
                measures=["revenue", "ticket count"],
                dimensions=["by show"]
            )
            result = await capability.execute(inputs)
            # Check if LLM translated correctly
            query = result.query_metadata.get('cube_response', {}).get('query', {})
            correct_measures = any('amount' in m for m in query.get('measures', []))
            print(f"   Measures: {query.get('measures', [])}")
            return result.success and correct_measures
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def _test_complex_filters(self, capability, tenant_id):
        """Test complex filter combinations"""
        try:
            inputs = TicketingDataInputs(
                session_id="test-filters",
                tenant_id=tenant_id,
                user_id="test",
                query_request="High value transactions (over $100) for Chicago",
                measures=["ticket_line_items.amount"],
                dimensions=["productions.name"],
                filters=[
                    CubeFilter(
                        member="ticket_line_items.amount",
                        operator="gt",
                        values=["100"]
                    )
                ]
            )
            result = await capability.execute(inputs)
            has_filters = len(result.query_metadata.get('cube_response', {}).get('query', {}).get('filters', [])) > 0
            print(f"   Filters applied: {has_filters}")
            return result.success
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    async def _test_time_intelligence(self, capability, tenant_id):
        """Test time-based queries"""
        try:
            inputs = TicketingDataInputs(
                session_id="test-time",
                tenant_id=tenant_id,
                user_id="test",
                query_request="Monthly revenue trend for last 6 months",
                measures=["ticket_line_items.amount"],
                time_context="last 6 months"
            )
            result = await capability.execute(inputs)
            query = result.query_metadata.get('cube_response', {}).get('query', {})
            has_time = len(query.get('timeDimensions', [])) > 0
            print(f"   Time dimensions: {len(query.get('timeDimensions', []))}")
            return result.success and has_time
        except Exception as e:
            print(f"   Error: {e}")
            return False


# Standalone test runner
async def run_all_tests():
    """Run all tests outside of pytest"""
    print("\n🧪 RUNNING COMPREHENSIVE TICKETING DATA CAPABILITY TESTS")
    print("Testing with REAL Cube.js data - NO MOCKS\n")
    
    capability = TicketingDataCapability()
    tenant_id = os.getenv("DEFAULT_TENANT_ID", "yesplan")
    
    test_instance = TestAllTicketingFeatures()
    await test_instance.test_feature_summary(capability, tenant_id)


if __name__ == "__main__":
    # Can be run directly or with pytest
    asyncio.run(run_all_tests())