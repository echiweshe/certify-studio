-- PostgreSQL Database Setup Script for Certify Studio
-- This script creates all necessary tables, indexes, and initial data

-- Create the database (if not exists)
-- Note: Run this separately if database doesn't exist:
-- CREATE DATABASE "Certify Studio Local" WITH ENCODING 'UTF8';

-- Connect to the database
\c "Certify Studio Local";

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Create schemas
CREATE SCHEMA IF NOT EXISTS certify_studio;
CREATE SCHEMA IF NOT EXISTS agent_data;
CREATE SCHEMA IF NOT EXISTS knowledge_graph;

-- Set search path
SET search_path TO certify_studio, public;

-- Drop existing tables (for clean setup)
DROP TABLE IF EXISTS generation_outputs CASCADE;
DROP TABLE IF EXISTS generation_stages CASCADE;
DROP TABLE IF EXISTS content_generations CASCADE;
DROP TABLE IF EXISTS agent_collaborations CASCADE;
DROP TABLE IF EXISTS agent_tasks CASCADE;
DROP TABLE IF EXISTS agent_metrics CASCADE;
DROP TABLE IF EXISTS agents CASCADE;
DROP TABLE IF EXISTS project_members CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    email_verified BOOLEAN DEFAULT false,
    settings JSONB DEFAULT '{}'::jsonb
);

-- User sessions
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API Keys
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    scopes TEXT[] DEFAULT ARRAY[]::TEXT[],
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id),
    settings JSONB DEFAULT '{}'::jsonb,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Project members
CREATE TABLE project_members (
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    added_by UUID REFERENCES users(id),
    PRIMARY KEY (project_id, user_id)
);

-- AI Agents
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'idle',
    capabilities JSONB DEFAULT '{}'::jsonb,
    configuration JSONB DEFAULT '{}'::jsonb,
    version VARCHAR(50),
    last_active TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_tasks_completed INTEGER DEFAULT 0,
    average_task_duration INTERVAL,
    success_rate DECIMAL(5,2)
);

-- Agent metrics
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2),
    metadata JSONB DEFAULT '{}'::jsonb,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agent tasks
CREATE TABLE agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id),
    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration INTERVAL GENERATED ALWAYS AS (completed_at - started_at) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agent collaborations
CREATE TABLE agent_collaborations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    primary_agent_id UUID NOT NULL REFERENCES agents(id),
    collaborating_agents UUID[] NOT NULL,
    collaboration_type VARCHAR(100) NOT NULL,
    purpose TEXT,
    outcome JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration INTERVAL GENERATED ALWAYS AS (ended_at - started_at) STORED
);

-- Content generations
CREATE TABLE content_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    title VARCHAR(500),
    input_files JSONB NOT NULL,
    output_format VARCHAR(50) NOT NULL,
    configuration JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    current_stage VARCHAR(100),
    quality_score DECIMAL(5,2),
    metadata JSONB DEFAULT '{}'::jsonb,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration INTERVAL GENERATED ALWAYS AS (completed_at - started_at) STORED
);

-- Generation stages
CREATE TABLE generation_stages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generation_id UUID NOT NULL REFERENCES content_generations(id) ON DELETE CASCADE,
    stage_name VARCHAR(100) NOT NULL,
    stage_order INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    agent_id UUID REFERENCES agents(id),
    input_data JSONB,
    output_data JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration INTERVAL GENERATED ALWAYS AS (completed_at - started_at) STORED,
    UNIQUE(generation_id, stage_order)
);

-- Generation outputs
CREATE TABLE generation_outputs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generation_id UUID NOT NULL REFERENCES content_generations(id) ON DELETE CASCADE,
    output_type VARCHAR(50) NOT NULL,
    file_path TEXT,
    file_size BIGINT,
    download_url TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Knowledge graph tables
CREATE TABLE knowledge_graph.concepts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    concept_type VARCHAR(100),
    domain VARCHAR(255),
    description TEXT,
    difficulty_level DECIMAL(3,2),
    metadata JSONB DEFAULT '{}'::jsonb,
    -- embedding vector(1536),  -- Requires pgvector extension
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Concept relationships
CREATE TABLE knowledge_graph.relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_concept_id UUID NOT NULL REFERENCES knowledge_graph.concepts(id),
    target_concept_id UUID NOT NULL REFERENCES knowledge_graph.concepts(id),
    relationship_type VARCHAR(100) NOT NULL,
    weight DECIMAL(3,2) DEFAULT 1.0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_concept_id, target_concept_id, relationship_type)
);

-- Learning paths
CREATE TABLE knowledge_graph.learning_paths (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    concept_sequence UUID[] NOT NULL,
    difficulty_curve JSONB,
    estimated_duration INTERVAL,
    prerequisites UUID[],
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_sessions_token ON user_sessions(token_hash);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_agents_type ON agents(agent_type);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agent_tasks_agent ON agent_tasks(agent_id);
CREATE INDEX idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX idx_generations_user ON content_generations(user_id);
CREATE INDEX idx_generations_status ON content_generations(status);
CREATE INDEX idx_generation_stages_generation ON generation_stages(generation_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- Text search indexes
CREATE INDEX idx_projects_search ON projects USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));
CREATE INDEX idx_concepts_search ON knowledge_graph.concepts USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));

-- Create triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_concepts_updated_at BEFORE UPDATE ON knowledge_graph.concepts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default agents
INSERT INTO agents (name, agent_type, capabilities, configuration) VALUES
('Content Generator', 'content_generator', 
 '{"formats": ["video", "interactive", "pdf", "vr"], "languages": ["en", "es", "fr"]}',
 '{"model": "gpt-4", "temperature": 0.7}'),
('Domain Extractor', 'domain_extractor',
 '{"extraction_types": ["comprehensive", "summary", "detailed"], "file_types": ["pdf", "docx", "txt"]}',
 '{"confidence_threshold": 0.8}'),
('Quality Assurance', 'quality_assurance',
 '{"checks": ["pedagogical", "technical", "accessibility", "completeness"]}',
 '{"standards": ["wcag_aa", "iso_9001"]}'),
('Export Manager', 'export_manager',
 '{"formats": ["scorm", "pdf", "video", "html5", "mobile"]}',
 '{"compression": true, "optimization": true}');

-- Create views for common queries
CREATE VIEW v_active_generations AS
SELECT 
    cg.*,
    u.email as user_email,
    u.full_name as user_name,
    p.name as project_name
FROM content_generations cg
LEFT JOIN users u ON cg.user_id = u.id
LEFT JOIN projects p ON cg.project_id = p.id
WHERE cg.status IN ('pending', 'processing');

CREATE VIEW v_agent_performance AS
SELECT 
    a.id,
    a.name,
    a.agent_type,
    a.status,
    COUNT(DISTINCT at.id) as total_tasks,
    COUNT(DISTINCT at.id) FILTER (WHERE at.status = 'completed') as completed_tasks,
    AVG(EXTRACT(EPOCH FROM at.duration)) as avg_duration_seconds,
    a.success_rate
FROM agents a
LEFT JOIN agent_tasks at ON a.id = at.agent_id
GROUP BY a.id;

-- Grant permissions (adjust as needed)
GRANT ALL ON SCHEMA certify_studio TO PUBLIC;
GRANT ALL ON SCHEMA agent_data TO PUBLIC;
GRANT ALL ON SCHEMA knowledge_graph TO PUBLIC;
GRANT ALL ON ALL TABLES IN SCHEMA certify_studio TO PUBLIC;
GRANT ALL ON ALL TABLES IN SCHEMA agent_data TO PUBLIC;
GRANT ALL ON ALL TABLES IN SCHEMA knowledge_graph TO PUBLIC;
GRANT ALL ON ALL SEQUENCES IN SCHEMA certify_studio TO PUBLIC;
GRANT ALL ON ALL SEQUENCES IN SCHEMA agent_data TO PUBLIC;
GRANT ALL ON ALL SEQUENCES IN SCHEMA knowledge_graph TO PUBLIC;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Certify Studio database schema created successfully!';
END $$;
