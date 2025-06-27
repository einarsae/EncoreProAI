-- EncoreProAI Database Initialization
-- Self-contained database setup with extensions and tables

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

-- Main entities table (based on old system analysis)
CREATE TABLE entities (
    tenant_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tenant_id, entity_type, id)
);

-- Production info table (matching old lookup store format)
CREATE TABLE production_info (
    tenant_id TEXT NOT NULL,
    id TEXT NOT NULL,
    name TEXT NOT NULL,
    first_date TEXT,
    last_date TEXT,
    total_revenue DECIMAL(15,2) DEFAULT 0,
    total_attendance INTEGER DEFAULT 0,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (tenant_id, id)
);

-- Indexes for entity resolution
CREATE INDEX idx_entities_trigram ON entities USING gin(name gin_trgm_ops);
CREATE INDEX idx_entities_type_tenant ON entities(tenant_id, entity_type);
CREATE INDEX idx_entities_name ON entities(name);

-- Indexes for production info
CREATE INDEX idx_production_info_dates ON production_info(first_date, last_date);
CREATE INDEX idx_production_info_revenue ON production_info(total_revenue DESC);
CREATE INDEX idx_production_info_tenant ON production_info(tenant_id);

-- Optional memories table for future memory service
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    user_id TEXT,
    tenant_id TEXT DEFAULT 'default',
    memory_type TEXT DEFAULT 'conversation',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for vector similarity search
CREATE INDEX idx_memories_embedding ON memories USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_memories_user ON memories(user_id);
CREATE INDEX idx_memories_tenant ON memories(tenant_id);
CREATE INDEX idx_memories_type ON memories(memory_type);

-- Note: Entity data will be populated from real Cube.js data using import scripts
-- No mock data inserted - use real data only

-- Sample domain knowledge for testing
INSERT INTO memories (content, memory_type, user_id, metadata) VALUES
    ('Revenue in theater means ticket sales amount, stored in ticket_line_items.amount', 'domain_knowledge', 'institutional', '{"concept": "revenue", "domain": "theater"}'),
    ('Attendance means number of tickets sold, stored in ticket_line_items.quantity', 'domain_knowledge', 'institutional', '{"concept": "attendance", "domain": "theater"}'),
    ('When users say performance they could mean revenue, attendance, or trends', 'domain_knowledge', 'institutional', '{"concept": "performance", "ambiguity": true}'),
    ('Broadway shows typically aim for 80%+ capacity for good performance', 'domain_knowledge', 'institutional', '{"concept": "good_performance", "benchmark": "80%"}'),
    ('Chicago has been running on Broadway since 1996, making it one of the longest-running shows', 'domain_knowledge', 'institutional', '{"entity": "chicago", "fact": "longest_running"}'),
    ('When users say Chicago without specifying, they usually mean the Broadway production unless discussing tours', 'domain_knowledge', 'institutional', '{"entity": "chicago", "disambiguation": "broadway_default"}');

-- Function to test trigram similarity with enhanced metadata
CREATE OR REPLACE FUNCTION test_entity_similarity(search_text TEXT, tenant TEXT DEFAULT 'test_tenant')
RETURNS TABLE(
    name TEXT, 
    entity_id TEXT,
    similarity_score REAL, 
    first_show TEXT,
    last_show TEXT,
    revenue DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.name,
        e.id,
        similarity(e.name, search_text) as similarity_score,
        pi.first_date,
        pi.last_date,
        pi.total_revenue
    FROM entities e
    LEFT JOIN production_info pi ON e.tenant_id = pi.tenant_id AND e.id = pi.id
    WHERE e.tenant_id = tenant
      AND e.entity_type = 'production'
      AND similarity(e.name, search_text) > 0.1
    ORDER BY similarity_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get entity disambiguation info
CREATE OR REPLACE FUNCTION get_entity_candidates(search_text TEXT, tenant TEXT DEFAULT 'test_tenant')
RETURNS TABLE(
    name TEXT,
    entity_id TEXT,
    disambiguation TEXT,
    confidence REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.name,
        e.id,
        CASE 
            WHEN pi.last_date = 'unknown' OR pi.last_date > TO_CHAR(CURRENT_DATE, 'YYYY-MM-DD') 
                THEN e.name || ' (Broadway, ' || COALESCE(SUBSTRING(pi.first_date, 1, 4), 'unknown') || '-present)'
            ELSE e.name || ' (Tour, ' || COALESCE(SUBSTRING(pi.first_date, 1, 4), 'unknown') || '-' || COALESCE(SUBSTRING(pi.last_date, 1, 4), 'unknown') || ')'
        END as disambiguation,
        -- Transform similarity score from 0.3-0.7 to 0.5-1.0 range (like old system)
        CASE 
            WHEN similarity(e.name, search_text) >= 0.7 THEN 1.0
            WHEN similarity(e.name, search_text) >= 0.5 THEN 0.8 + (similarity(e.name, search_text) - 0.5) * 1.0
            ELSE 0.5 + (similarity(e.name, search_text) - 0.3) * 0.75
        END as confidence
    FROM entities e
    LEFT JOIN production_info pi ON e.tenant_id = pi.tenant_id AND e.id = pi.id
    WHERE e.tenant_id = tenant
      AND e.entity_type = 'production'
      AND similarity(e.name, search_text) > 0.3
    ORDER BY confidence DESC;
END;
$$ LANGUAGE plpgsql;