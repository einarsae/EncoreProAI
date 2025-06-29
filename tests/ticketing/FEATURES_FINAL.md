# TicketingDataCapability - Final Feature Documentation

## ✅ All Features Working (9/9)

### 1. **Basic Queries** ✅
- Standard measures and dimensions
- Proper ordering and limits
- All field names from schema

### 2. **Multi-fetch Strategy** ✅
- Automatically splits queries for time comparisons
- Handles Q1 vs Q2, year-over-year comparisons
- Executes up to 3 queries in parallel
- Saves orchestrator roundtrips

### 3. **Pagination** ✅
- `offset`: Skip rows for pagination
- `limit`: Control result size
- Automatic ordering when limit applied

### 4. **Total Count** ✅
- `total: true` for pagination UI needs
- LLM adds when user mentions "pagination"

### 5. **Hierarchical Data** ✅
- Multiple dimensions for hierarchy
- Example: retailers.name → sales_channels.name → productions.name
- No drilldown parameter needed (not supported by our Cube.js)

### 6. **High Cardinality Handling** ✅
- Automatically limits city/postcode queries
- Smart handling of customer_id dimensions
- Memory-aware query generation

### 7. **Natural Language Understanding** ✅
- Translates common terms:
  - "revenue" → ticket_line_items.amount
  - "attendance" → ticket_line_items.quantity
  - "by show" → productions.name
- Handles various time expressions

### 8. **Complex Filters** ✅
- Nested AND/OR logic
- Post-aggregation filters
- All Cube.js operators supported
- Entity ID filtering for precision

### 9. **Time Intelligence** ✅
- Natural language time parsing
- Granularity selection (day/week/month/quarter/year)
- Time-based grouping and filtering

## 🚫 Features NOT Supported by Our Cube.js Instance

### 1. **Drilldown Parameter**
- API returns: "drilldown is not allowed"
- **Solution**: Use multiple dimensions instead

### 2. **Ungrouped Queries**
- Raw data export requires specific setup
- **Solution**: Use fine-grained dimensions

### 3. **venues Cube**
- No separate venues cube exists
- **Solution**: Use ticket_line_items.venue_id

## 📝 Key Learnings

1. **Simple Prompts Win**: Reduced from 330+ lines to ~80 lines
2. **No Prompt Stacking**: Clear, non-conflicting rules
3. **Trust the LLM**: Let it understand intent naturally
4. **Real Testing**: No mocks revealed actual API limitations
5. **Multi-fetch Value**: Essential for comparison queries

## 🎯 Best Practices

1. **Use exact field names when possible**
   ```
   ticket_line_items.amount (not "revenue")
   ticket_line_items.quantity (not "attendance")
   ```

2. **Let LLM handle natural language**
   - User says "top venues" → LLM adds order and limit
   - User says "compare quarters" → LLM uses multi-fetch

3. **Memory awareness for high cardinality**
   - Cities, postcodes, customers need limits
   - Event-level data benefits from coarser granularity

4. **Hierarchical queries without drilldown**
   ```json
   {
     "dimensions": ["retailers.name", "sales_channels.name"],
     "measures": ["ticket_line_items.amount"]
   }
   ```

## 🚀 Production Ready

The TicketingDataCapability is now production-ready with:
- All major features working
- Comprehensive test coverage
- Clear documentation
- Memory-aware query generation
- Natural language understanding
- Multi-fetch for complex comparisons

Next step: Implement EventAnalysisCapability to analyze the data this capability fetches!