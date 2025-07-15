# PostgreSQL Database Setup Guide for Certify Studio

## Overview

This guide provides comprehensive instructions for setting up PostgreSQL as the database backend for Certify Studio. PostgreSQL offers superior performance, scalability, and features compared to SQLite, making it ideal for production deployments.

## Prerequisites

1. **PostgreSQL 13+** installed and running
2. **Python 3.8+** with pip
3. **pgAdmin 4** (already installed based on your screenshot)
4. Administrative access to PostgreSQL

## Quick Start

### 1. Automated Setup

Run the automated setup script:

```bash
cd scripts/database
setup_postgresql.bat
```

This will:
- Connect to your PostgreSQL server
- Create the "Certify Studio Local" database (if needed)
- Create all required schemas and tables
- Set up indexes for optimal performance
- Insert sample data
- Configure the application

### 2. Manual Setup (Alternative)

If you prefer manual setup or the automated script fails:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE "Certify Studio Local" WITH ENCODING 'UTF8';

# Run schema creation
psql -U postgres -d "Certify Studio Local" -f 01_create_schema.sql

# Add sample data
psql -U postgres -d "Certify Studio Local" -f 02_seed_data.sql

# Apply performance optimizations
psql -U postgres -d "Certify Studio Local" -f 03_optimize_performance.sql
```

## Database Structure

### Schemas

1. **certify_studio** - Main application schema
   - Users, projects, content generations
   - Agent tasks and collaborations
   - Audit logs

2. **agent_data** - Agent-specific data
   - Agent metrics
   - Performance statistics

3. **knowledge_graph** - Knowledge representation
   - Concepts and relationships
   - Learning paths

### Key Tables

#### Core Tables
- `users` - User accounts and authentication
- `projects` - Learning projects
- `content_generations` - Generated content tracking
- `agents` - AI agent registry
- `agent_tasks` - Agent task history

#### Knowledge Graph
- `concepts` - Knowledge concepts
- `relationships` - Concept relationships
- `learning_paths` - Curated learning sequences

## Configuration

### Environment Variables

The setup script creates `.env.postgresql` with:

```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_NAME="Certify Studio Local"
DATABASE_URL="postgresql://postgres:password@localhost:5432/Certify Studio Local"
```

### Application Configuration

Update your main `.env` file to use PostgreSQL:

```env
# Replace SQLite URL with PostgreSQL
DATABASE_URL="postgresql://postgres:password@localhost:5432/Certify Studio Local"
```

## Security

### Default Users

The seed data creates three test users:
- **Admin**: admin@certifystudio.com / password123
- **Instructor**: instructor@certifystudio.com / password123
- **Student**: student@certifystudio.com / password123

**⚠️ Change these passwords immediately in production!**

### Best Practices

1. **Use Strong Passwords**: Change default passwords
2. **Limit Connections**: Configure pg_hba.conf appropriately
3. **SSL/TLS**: Enable encrypted connections
4. **Regular Backups**: Set up automated backups

## Performance Optimization

### Indexes

The setup includes optimized indexes for:
- User authentication queries
- Content generation lookups
- Agent task tracking
- Knowledge graph traversal
- Full-text search

### Maintenance

Run maintenance tasks periodically:

```sql
-- Run maintenance function
SELECT * FROM perform_maintenance();

-- Refresh dashboard statistics
SELECT refresh_dashboard_stats();
```

### Monitoring

Check database health:

```bash
psql -U postgres -d "Certify Studio Local" -f health_check.sql
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check PostgreSQL is running: `pg_ctl status`
   - Verify pg_hba.conf allows connections
   - Check firewall settings

2. **Permission Denied**
   - Ensure user has CREATEDB privilege
   - Check schema permissions

3. **Script Errors**
   - Run scripts in order (01, 02, 03)
   - Check PostgreSQL version compatibility

### Logs

PostgreSQL logs location:
- Windows: `C:\Program Files\PostgreSQL\15\data\log\`
- Linux: `/var/log/postgresql/`

## Backup and Recovery

### Backup

```bash
# Full backup
pg_dump -U postgres -d "Certify Studio Local" -f backup.sql

# Compressed backup
pg_dump -U postgres -d "Certify Studio Local" -Fc -f backup.dump
```

### Restore

```bash
# From SQL file
psql -U postgres -d "Certify Studio Local" -f backup.sql

# From compressed dump
pg_restore -U postgres -d "Certify Studio Local" backup.dump
```

## Migration from SQLite

If migrating from SQLite:

1. Export SQLite data
2. Transform data format if needed
3. Import into PostgreSQL
4. Update application configuration

## Advanced Features

### Full-Text Search

```sql
-- Example: Search projects
SELECT * FROM projects
WHERE to_tsvector('english', name || ' ' || description) 
@@ plainto_tsquery('english', 'aws certification');
```

### JSON Queries

```sql
-- Example: Query agent capabilities
SELECT * FROM agents
WHERE capabilities @> '{"formats": ["video"]}';
```

### Materialized Views

Dashboard statistics are cached in materialized views for performance:

```sql
-- Refresh statistics
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_stats;
```

## Integration with Certify Studio

After setup:

1. Restart the backend:
   ```bash
   uv run uvicorn certify_studio.main:app --reload
   ```

2. Verify connection:
   ```bash
   python tests/test_backend_connectivity.py
   ```

3. Run tests:
   ```bash
   test_aws_workflow.bat
   ```

## Maintenance Schedule

### Daily
- Check active connections
- Monitor slow queries
- Review error logs

### Weekly
- Run VACUUM ANALYZE
- Update table statistics
- Check index usage

### Monthly
- Full backup
- Performance review
- Schema optimization

## Support

For issues:
1. Check health_check.sql output
2. Review PostgreSQL logs
3. Verify configuration files
4. Test connection with pgAdmin

---

**Last Updated**: January 2025
**Database Version**: PostgreSQL 15
**Schema Version**: 1.0.0
