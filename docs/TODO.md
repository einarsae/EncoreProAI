# TODO - Development Priorities

## 🚨 Critical Fixes

### 1. Fix Infinite Orchestration Loop 🚧 IN PROGRESS
**Issue**: Orchestrator sometimes doesn't complete, keeps looping
**Files**: `workflow/nodes.py`, `workflow/graph.py`
**Investigation**:
  - Loop counter is in place but may need adjustment
  - Need to ensure "complete" action is properly triggered
  - Check if capability results are being interpreted correctly

### 2. Add Query Result Limits ❌ NOT STARTED
**Issue**: No limits on query results could exhaust memory
**Files**: All capabilities need limits
**Required**:
  - Add max_results parameter to capabilities
  - Implement pagination hints in results
  - Test with large datasets

## 🎯 Feature Development Priorities

### Phase 1: Core Functionality ✅ MOSTLY COMPLETE
- [✅] Fix multi-fetch bug - DONE! All 9/9 features working
- [✅] Implement EventAnalysisCapability MVP - DONE! 250 lines, structured output
- [✅] Test full orchestration flow - DONE! All capabilities integrated
- [✅] Dynamic capability descriptions - DONE! 100% routing accuracy
- [✅] Fix data format issues - DONE! Root causes fixed
- [✅] Integrate ChatCapability - DONE! Emotional support working
- [🚧] Fix infinite orchestration loop - IN PROGRESS
- [❌] Add query limits - NOT STARTED

### Phase 2: Context Tools (Next Priority)
- [ ] DataContextTool for dimension summaries
  - Pre-calculate available values for each dimension
  - Help prevent invalid queries
  - Reduce back-and-forth with orchestrator
- [ ] TimeRangeContextTool for data availability
  - Check what time ranges have data
  - Prevent queries for non-existent periods
  - Guide time-based analysis

### Phase 3: Advanced Features (Future)
- [ ] Complete memory learning system
  - Pattern recognition from successful queries
  - User preference learning
  - Domain knowledge accumulation
- [ ] Multi-frame query handling
  - Support complex multi-part questions
  - Maintain context across frames
- [ ] Enhanced analysis capabilities
  - Customer segmentation analysis
  - Cohort analysis
  - Predictive insights
  - Trend detection and anomaly identification

### Phase 3: Intelligence & Learning (Next)
- [ ] Adaptive query optimization based on usage patterns
- [ ] Automatic insight discovery
- [ ] Natural language report generation
- [ ] Visualization recommendations

### Phase 4: Production Deployment (After All Features)
- [ ] Production deployment setup
- [ ] Documentation for deployment
- [ ] Security review
- [ ] Performance baseline

## 🚫 Deprioritized (Infrastructure Can Wait)
- ~~Schema caching~~ (not critical)
- ~~Rate limiting~~ (Cube.js handles this)
- ~~Query result caching~~ (premature optimization)
- ~~Monitoring/metrics~~ (can add when deploying)

## 📝 Notes
- Focus on delivering value through features, not infrastructure
- Memory learning and multi-frame handling unlock new capabilities
- Customer segmentation is a key differentiator
- Infrastructure improvements only when actually needed