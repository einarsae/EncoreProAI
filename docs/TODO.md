# TODO - Development Priorities

## 🚨 Critical Fixes

### 1. ~~Fix Multi-fetch Granularity Bug~~ ✅ COMPLETED
**File**: `capabilities/ticketing_data.py`  
**Solution**: Updated prompts to clarify granularity handling  
**Result**: All 9/9 features working + code cleaned up (674 lines, was 853)

### 2. ~~Implement EventAnalysisCapability (Simple MVP)~~ ✅ COMPLETED
**File**: `capabilities/event_analysis.py`  
**Result**: Clean MVP implementation with structured output
**What We Built**:
  - 250 lines of clean code
  - Structured output with Pydantic
  - Progressive data requests working
  - Full test coverage
**Future Enhancements** (only add if needed):
  - Context tools (if >3 data request loops)
  - Memory integration (if patterns repeat >10 times)
  - Statistical tools (if LLM math proves wrong)

## 🎯 Feature Development Priorities

### Phase 1: Core Functionality (Immediate)
- [✅] Fix multi-fetch bug - DONE! All 9/9 features working
- [✅] Implement EventAnalysisCapability MVP - DONE! 250 lines, structured output
- [ ] **NEXT: Test full orchestration flow with all capabilities**
  - Wire up EventAnalysisCapability in orchestrator
  - Test progressive analysis (EAC → TDC → EAC → complete)
  - Ensure entity IDs flow correctly
- [ ] Integrate ChatCapability with orchestrator

### Phase 2: Advanced Features (High Priority)
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