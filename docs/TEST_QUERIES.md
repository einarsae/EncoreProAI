# EncoreProAI - Test Query Suite

## Overview

ALL queries must work with 100% success rate using REAL DATA from our database.

## Available Test Data

From our actual database:
- **Shows**: Gatsby, Hell's Kitchen, Outsiders, Some Like It Hot, Chicago
- **No access to**: Hamilton, Lion King (not in our DB)

## Query Categories

### 1. Companionship & Chat (NEW - CRITICAL)

#### Emotional Support
- ✅ "I'm feeling overwhelmed with all these numbers"
- ✅ "This is stressful, help me understand what to focus on"
- ✅ "I don't know where to start with analyzing my shows"
- ✅ "Tell me something positive about our performance"

#### Follow-up Generation
- ✅ "What else should I be looking at?"
- ✅ "What questions should I ask about my data?"
- ✅ "Help me dig deeper into this"

#### General Conversation
- ✅ "Tell me about the theater industry"
- ✅ "What makes a show successful?"
- ✅ "How do you think about audience engagement?"

### 2. Simple Data Retrieval

#### Basic Aggregations
- ✅ "What is the total revenue for Gatsby?"
- ✅ "How many tickets were sold for Hell's Kitchen?"
- ✅ "Show me attendance for Outsiders"
- ✅ "What is the average ticket price for Chicago?"
- ✅ "Total revenue across all shows"

#### Time-Based Queries
- ✅ "Revenue for Some Like It Hot in January 2024"
- ✅ "Show me last week's ticket sales"
- ✅ "How many tickets sold yesterday?"
- ✅ "What were last month's sales?"

#### Entity-Specific Queries
- ✅ "Which venues are we operating?"
- ✅ "List all current productions"
- ✅ "Show me all the places we sell tickets"

### 3. Comparison Queries

#### Show Comparisons
- ✅ "Compare sales for Hell's Kitchen and Chicago"
- ✅ "Gatsby vs Outsiders revenue last quarter"
- ✅ "Which show performed better: Hell's Kitchen or Some Like It Hot?"
- ✅ "Compare all shows by attendance"

#### Time Comparisons
- ✅ "This month vs last month revenue"
- ✅ "Compare Q4 2023 to Q4 2024"
- ✅ "Year-over-year growth for Gatsby"
- ✅ "Weekend vs weekday sales for all shows"

### 4. Trend Analysis

#### Performance Trends
- ✅ "Show revenue trends for Outsiders over the past 6 months"
- ✅ "How has attendance changed for Chicago since opening?"
- ✅ "Monthly ticket sales trend for all productions"
- ✅ "Is Hell's Kitchen revenue declining?"

#### Seasonal Patterns
- ✅ "How do holidays affect ticket sales?"
- ✅ "Summer vs winter attendance patterns"
- ✅ "Best performing months historically"

### 5. Complex Analysis (LLM Decides Approach)

#### Flexible Performance Analysis
- ✅ "Which shows need attention?" (LLM decides criteria)
- ✅ "Find opportunities in our data" (LLM explores)
- ✅ "What's interesting about Gatsby's performance?" (LLM analyzes)
- ✅ "How are our shows doing?" (LLM determines metrics)

#### Pattern Detection
- ✅ "What patterns do you see in our sales?"
- ✅ "Find anomalies in ticket purchases"
- ✅ "Identify trends I should know about"

### 6. Customer Analysis

#### Basic Segmentation
- ✅ "How many unique customers last month?"
- ✅ "What percentage are repeat buyers?"
- ✅ "Average spend per customer"
- ✅ "New vs returning customer ratio"

#### Behavioral Analysis
- ✅ "Which customers buy premium seats?"
- ✅ "Customers who attend multiple shows"
- ✅ "Most loyal customer segments"

### 7. Ambiguity Handling

#### Entity Ambiguity
- ✅ "Show me Chicago data" (the show, with assumption sharing)
- ✅ "Performance last week" (which show? what metric?)
- ✅ "Compare our best shows" (define "best")

#### Metric Ambiguity
- ✅ "How are we doing?" (what metric?)
- ✅ "Show performance" (sales? attendance? trends?)
- ✅ "Success metrics" (what defines success?)

### 8. Multi-Turn Conversations

#### Context Preservation
```
Turn 1: "Show me Gatsby revenue"
Turn 2: "How about last month?" (remembers Gatsby)
Turn 3: "Compare to Hell's Kitchen" (remembers timeframe)
Turn 4: "What drives the difference?" (remembers comparison)
```

#### Clarification Flows
```
User: "Show me performance"
System: "I can show you performance data. Are you interested in revenue, attendance, or trends?"
User: "Revenue"
System: [Shows revenue data with assumptions noted]
```

### 9. Queries Needing Alternative Approaches

Since web search is removed, these need creative solutions:
- ✅ "How do we compare to Broadway averages?" → Use historical data
- ✅ "What are critics saying?" → Suggest checking external sources
- ✅ "Market trends" → Analyze our own data trends

## Success Criteria

Each query must:
1. Return accurate data from real database
2. Share assumptions made
3. Provide appropriate emotional tone (for chat)
4. Generate useful follow-ups
5. Complete in reasonable time

## Test Execution

```python
async def test_all_queries():
    """Test with real database connection"""
    
    # Test companionship first (new critical feature)
    await test_emotional_support()
    await test_follow_up_generation()
    
    # Test data queries
    await test_simple_queries()
    await test_comparisons()
    await test_flexible_analysis()
    
    # Test sophisticated features
    await test_ambiguity_handling()
    await test_multi_turn_memory()
    
    # Must achieve 100% success rate
```

## Notes

- NO MOCK DATA - all tests use real database
- Test with actual show names (Gatsby, not Hamilton)
- Verify JWT tenant isolation works
- Check assumption sharing on ambiguous queries
- Ensure emotional tone in chat responses