-- Seed data for Certify Studio PostgreSQL database
-- This script adds sample data for testing

-- Use the correct schema
SET search_path TO certify_studio, public;

-- Insert sample users (passwords are hashed versions of 'password123')
INSERT INTO users (email, username, password_hash, full_name, is_active, is_superuser) VALUES
('admin@certifystudio.com', 'admin', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Admin User', true, true),
('instructor@certifystudio.com', 'instructor', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'Sarah Johnson', true, false),
('student@certifystudio.com', 'student', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'John Doe', true, false)
ON CONFLICT (email) DO NOTHING;

-- Insert sample projects
INSERT INTO projects (name, description, owner_id, tags, is_public) 
SELECT 
    'AWS AI Practitioner Certification Prep',
    'Comprehensive course for AWS AI Practitioner (AIF-C01) certification exam preparation',
    u.id,
    ARRAY['aws', 'ai', 'certification', 'cloud'],
    true
FROM users u WHERE u.email = 'instructor@certifystudio.com'
ON CONFLICT DO NOTHING;

INSERT INTO projects (name, description, owner_id, tags, is_public)
SELECT 
    'Azure AI Fundamentals',
    'Introduction to Azure AI services and machine learning concepts',
    u.id,
    ARRAY['azure', 'ai', 'fundamentals', 'microsoft'],
    true
FROM users u WHERE u.email = 'instructor@certifystudio.com'
ON CONFLICT DO NOTHING;

-- Add sample knowledge graph concepts
INSERT INTO knowledge_graph.concepts (name, concept_type, domain, description, difficulty_level) VALUES
('Machine Learning', 'fundamental', 'ai', 'The study of computer algorithms that improve automatically through experience', 0.3),
('Deep Learning', 'fundamental', 'ai', 'A subset of machine learning based on artificial neural networks', 0.6),
('Neural Networks', 'fundamental', 'ai', 'Computing systems inspired by biological neural networks', 0.5),
('Natural Language Processing', 'application', 'ai', 'AI technology for understanding and generating human language', 0.7),
('Computer Vision', 'application', 'ai', 'AI technology for understanding and analyzing visual information', 0.7),
('AWS SageMaker', 'service', 'aws', 'Fully managed machine learning service by AWS', 0.5),
('Amazon Rekognition', 'service', 'aws', 'Deep learning-based image and video analysis service', 0.4),
('Amazon Comprehend', 'service', 'aws', 'Natural language processing service for text analysis', 0.4),
('Amazon Lex', 'service', 'aws', 'Service for building conversational interfaces', 0.5),
('Amazon Polly', 'service', 'aws', 'Text-to-speech service using deep learning', 0.3)
ON CONFLICT DO NOTHING;

-- Add relationships between concepts
INSERT INTO knowledge_graph.relationships (source_concept_id, target_concept_id, relationship_type, weight)
SELECT 
    c1.id, c2.id, 'prerequisite', 0.9
FROM knowledge_graph.concepts c1, knowledge_graph.concepts c2
WHERE c1.name = 'Machine Learning' AND c2.name = 'Deep Learning'
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_graph.relationships (source_concept_id, target_concept_id, relationship_type, weight)
SELECT 
    c1.id, c2.id, 'prerequisite', 0.8
FROM knowledge_graph.concepts c1, knowledge_graph.concepts c2
WHERE c1.name = 'Neural Networks' AND c2.name = 'Deep Learning'
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_graph.relationships (source_concept_id, target_concept_id, relationship_type, weight)
SELECT 
    c1.id, c2.id, 'implements', 0.9
FROM knowledge_graph.concepts c1, knowledge_graph.concepts c2
WHERE c1.name = 'Amazon Rekognition' AND c2.name = 'Computer Vision'
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_graph.relationships (source_concept_id, target_concept_id, relationship_type, weight)
SELECT 
    c1.id, c2.id, 'implements', 0.9
FROM knowledge_graph.concepts c1, knowledge_graph.concepts c2
WHERE c1.name = 'Amazon Comprehend' AND c2.name = 'Natural Language Processing'
ON CONFLICT DO NOTHING;

-- Add sample agent metrics
INSERT INTO agent_metrics (agent_id, metric_type, metric_value, metadata)
SELECT 
    a.id, 'task_completion_rate', 95.5, '{"period": "last_7_days"}'::jsonb
FROM agents a WHERE a.agent_type = 'content_generator'
ON CONFLICT DO NOTHING;

INSERT INTO agent_metrics (agent_id, metric_type, metric_value, metadata)
SELECT 
    a.id, 'average_response_time', 2.3, '{"unit": "seconds", "period": "last_24_hours"}'::jsonb
FROM agents a WHERE a.agent_type = 'domain_extractor'
ON CONFLICT DO NOTHING;

-- Update agent statistics
UPDATE agents SET
    status = 'idle',
    last_active = CURRENT_TIMESTAMP - INTERVAL '5 minutes',
    total_tasks_completed = 150,
    average_task_duration = INTERVAL '3 minutes 25 seconds',
    success_rate = 98.5
WHERE agent_type = 'content_generator';

UPDATE agents SET
    status = 'idle',
    last_active = CURRENT_TIMESTAMP - INTERVAL '10 minutes',
    total_tasks_completed = 200,
    average_task_duration = INTERVAL '45 seconds',
    success_rate = 99.2
WHERE agent_type = 'domain_extractor';

-- Create a sample learning path
INSERT INTO knowledge_graph.learning_paths (name, description, concept_sequence, estimated_duration)
SELECT 
    'AWS AI Services Fundamentals',
    'Learn the basics of AWS AI services for the certification exam',
    ARRAY[
        (SELECT id FROM knowledge_graph.concepts WHERE name = 'Machine Learning'),
        (SELECT id FROM knowledge_graph.concepts WHERE name = 'Neural Networks'),
        (SELECT id FROM knowledge_graph.concepts WHERE name = 'Deep Learning'),
        (SELECT id FROM knowledge_graph.concepts WHERE name = 'Computer Vision'),
        (SELECT id FROM knowledge_graph.concepts WHERE name = 'Amazon Rekognition'),
        (SELECT id FROM knowledge_graph.concepts WHERE name = 'Natural Language Processing'),
        (SELECT id FROM knowledge_graph.concepts WHERE name = 'Amazon Comprehend')
    ],
    INTERVAL '8 hours'
ON CONFLICT DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Sample data inserted successfully!';
END $$;
