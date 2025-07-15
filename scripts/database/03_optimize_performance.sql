-- Performance optimization for Certify Studio PostgreSQL database

SET search_path TO certify_studio, public;

-- Additional indexes for common queries
-- Note: Remove CONCURRENTLY for initial setup
CREATE INDEX IF NOT EXISTS idx_generations_created_at 
ON content_generations(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_tasks_created_at 
ON agent_tasks(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_sessions_expires 
ON user_sessions(expires_at);

-- Partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_active_generations 
ON content_generations(status, created_at DESC) 
WHERE status IN ('pending', 'processing');

CREATE INDEX IF NOT EXISTS idx_active_agents 
ON agents(status) 
WHERE status = 'active';

-- Composite indexes for joins
CREATE INDEX IF NOT EXISTS idx_generation_stages_composite 
ON generation_stages(generation_id, stage_order);

CREATE INDEX IF NOT EXISTS idx_project_members_composite 
ON project_members(user_id, project_id);

-- JSON indexes for metadata queries
CREATE INDEX IF NOT EXISTS idx_generations_metadata 
ON content_generations USING gin(metadata);

CREATE INDEX IF NOT EXISTS idx_agents_capabilities 
ON agents USING gin(capabilities);

-- Create materialized view for dashboard statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_stats AS
SELECT 
    COUNT(DISTINCT u.id) as total_users,
    COUNT(DISTINCT p.id) as total_projects,
    COUNT(DISTINCT cg.id) as total_generations,
    COUNT(DISTINCT cg.id) FILTER (WHERE cg.created_at > CURRENT_DATE - INTERVAL '7 days') as generations_last_week,
    COUNT(DISTINCT cg.id) FILTER (WHERE cg.status = 'completed') as completed_generations,
    AVG(cg.quality_score) FILTER (WHERE cg.quality_score IS NOT NULL) as avg_quality_score,
    COUNT(DISTINCT at.id) as total_agent_tasks,
    AVG(EXTRACT(EPOCH FROM at.duration)) FILTER (WHERE at.duration IS NOT NULL) as avg_task_duration_seconds
FROM users u
CROSS JOIN projects p
CROSS JOIN content_generations cg
CROSS JOIN agent_tasks at;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_dashboard_stats ON mv_dashboard_stats(total_users);

-- Function to refresh dashboard stats
CREATE OR REPLACE FUNCTION refresh_dashboard_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_dashboard_stats;
END;
$$ LANGUAGE plpgsql;

-- Partitioning for large tables (audit logs)
-- Create partition function
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name text, start_date date)
RETURNS void AS $$
DECLARE
    partition_name text;
    start_date_str text;
    end_date_str text;
BEGIN
    partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM');
    start_date_str := to_char(start_date, 'YYYY-MM-DD');
    end_date_str := to_char(start_date + interval '1 month', 'YYYY-MM-DD');
    
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
        FOR VALUES FROM (%L) TO (%L)',
        partition_name, table_name, start_date_str, end_date_str
    );
END;
$$ LANGUAGE plpgsql;

-- Vacuum and analyze configuration
-- Note: These are recommendations, actual changes need to be made to postgresql.conf
-- ALTER TABLE content_generations SET (autovacuum_vacuum_scale_factor = 0.1);
-- ALTER TABLE agent_tasks SET (autovacuum_vacuum_scale_factor = 0.1);
-- ALTER TABLE audit_logs SET (autovacuum_vacuum_scale_factor = 0.05);

-- Connection pooling recommendations (add to postgresql.conf)
COMMENT ON DATABASE "Certify Studio Local" IS 
'Recommended settings:
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
wal_buffers = 16MB
checkpoint_completion_target = 0.9';

-- Create database maintenance function
CREATE OR REPLACE FUNCTION perform_maintenance()
RETURNS TABLE(
    operation text,
    status text
) AS $$
BEGIN
    -- Vacuum analyze main tables
    RETURN QUERY SELECT 'VACUUM ANALYZE users', 'starting'::text;
    VACUUM ANALYZE users;
    RETURN QUERY SELECT 'VACUUM ANALYZE users', 'completed'::text;
    
    RETURN QUERY SELECT 'VACUUM ANALYZE content_generations', 'starting'::text;
    VACUUM ANALYZE content_generations;
    RETURN QUERY SELECT 'VACUUM ANALYZE content_generations', 'completed'::text;
    
    RETURN QUERY SELECT 'VACUUM ANALYZE agent_tasks', 'starting'::text;
    VACUUM ANALYZE agent_tasks;
    RETURN QUERY SELECT 'VACUUM ANALYZE agent_tasks', 'completed'::text;
    
    -- Refresh materialized views
    RETURN QUERY SELECT 'REFRESH mv_dashboard_stats', 'starting'::text;
    REFRESH MATERIALIZED VIEW mv_dashboard_stats;
    RETURN QUERY SELECT 'REFRESH mv_dashboard_stats', 'completed'::text;
    
    -- Clean up old sessions
    RETURN QUERY SELECT 'Clean expired sessions', 'starting'::text;
    DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP;
    RETURN QUERY SELECT 'Clean expired sessions', 'completed'::text;
    
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION perform_maintenance() TO PUBLIC;
GRANT EXECUTE ON FUNCTION refresh_dashboard_stats() TO PUBLIC;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Performance optimizations applied successfully!';
    RAISE NOTICE 'Run SELECT * FROM perform_maintenance(); periodically for maintenance';
END $$;
