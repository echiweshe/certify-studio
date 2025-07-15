-- Quick database health check and statistics

SET search_path TO certify_studio, public;

-- Database size
SELECT 
    pg_database.datname as database_name,
    pg_size_pretty(pg_database_size(pg_database.datname)) as size
FROM pg_database
WHERE datname = 'Certify Studio Local';

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as indexes_size
FROM pg_tables
WHERE schemaname IN ('certify_studio', 'knowledge_graph', 'agent_data')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Row counts
SELECT 
    'users' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'projects', COUNT(*) FROM projects
UNION ALL
SELECT 'content_generations', COUNT(*) FROM content_generations
UNION ALL
SELECT 'agents', COUNT(*) FROM agents
UNION ALL
SELECT 'agent_tasks', COUNT(*) FROM agent_tasks
UNION ALL
SELECT 'concepts', COUNT(*) FROM knowledge_graph.concepts
UNION ALL
SELECT 'relationships', COUNT(*) FROM knowledge_graph.relationships;

-- Active connections
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    state_change
FROM pg_stat_activity
WHERE datname = 'Certify Studio Local'
AND state != 'idle'
ORDER BY query_start DESC;

-- Recent activity
SELECT 
    'Recent Generations' as activity,
    COUNT(*) as count
FROM content_generations
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
UNION ALL
SELECT 
    'Recent Agent Tasks',
    COUNT(*)
FROM agent_tasks
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
UNION ALL
SELECT 
    'Active Users (24h)',
    COUNT(DISTINCT user_id)
FROM user_sessions
WHERE last_activity > CURRENT_TIMESTAMP - INTERVAL '24 hours';

-- Agent status
SELECT 
    name,
    agent_type,
    status,
    total_tasks_completed,
    success_rate,
    last_active
FROM agents
ORDER BY last_active DESC;

-- Index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname IN ('certify_studio', 'knowledge_graph')
ORDER BY idx_scan DESC
LIMIT 10;

-- Slow queries (if pg_stat_statements is enabled)
-- SELECT query, calls, mean_exec_time, total_exec_time
-- FROM pg_stat_statements
-- WHERE query NOT LIKE '%pg_stat_statements%'
-- ORDER BY mean_exec_time DESC
-- LIMIT 5;
