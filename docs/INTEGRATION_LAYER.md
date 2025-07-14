# Integration Layer Documentation

## Overview

The integration layer connects all components of Certify Studio:
- Database repositories
- API endpoints
- Background tasks
- Agent orchestration
- Event-driven workflows

## Architecture

```
┌─────────────────────┐
│   API Endpoints     │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Service Layer      │ ◄─── Business Logic
└──────────┬──────────┘
           │
     ┌─────┴─────┬─────────┬──────────┐
     │           │         │          │
┌────▼────┐ ┌───▼────┐ ┌──▼───┐ ┌───▼────┐
│Database │ │ Agents │ │Events│ │ Celery │
└─────────┘ └────────┘ └──────┘ └────────┘
```

## Key Components

### 1. Dependencies (`dependencies.py`)
- **Database Sessions**: Managed lifecycle with auto-commit/rollback
- **Authentication**: JWT token validation and user extraction
- **Authorization**: Permission checking with RBAC
- **Repository Injection**: Clean dependency injection for data access

### 2. Services (`services.py`)
- **ContentGenerationService**: Orchestrates entire content generation workflow
- **DomainExtractionService**: Manages knowledge extraction
- **QualityAssuranceService**: Handles quality checks and feedback
- **UserService**: User management and authentication
- **AnalyticsService**: Metrics and reporting

### 3. Background Tasks (`background.py`)
- **Celery Integration**: Distributed task processing
- **Task Types**:
  - Content generation processing
  - Domain extraction
  - Quality checks
  - Export tasks
  - Maintenance tasks

### 4. Event System (`events.py`)
- **Event Bus**: Decoupled communication
- **Event Types**: Generation, quality, user, analytics events
- **Handlers**: Logging, metrics, notifications

## Usage Examples

### Starting Content Generation

```python
# In API endpoint
async def generate_content(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    service = ContentGenerationService(db)
    
    # Start generation (creates DB record + background task)
    generation = await service.start_generation(
        user=current_user,
        source_file=file.file,
        filename=file.filename,
        title="AWS Certification",
        content_type=ContentType.FULL_CERTIFICATION
    )
    
    return generation
```

### Processing in Background

```python
# Automatically called by Celery
@celery_app.task
async def process_content_generation(generation_id: str):
    async with get_db_session() as db:
        service = ContentGenerationService(db.session)
        
        # This orchestrates:
        # 1. Domain extraction
        # 2. Content generation with agents
        # 3. Quality checks
        # 4. Event emissions
        result = await service.process_generation(UUID(generation_id))
```

### Event-Driven Updates

```python
# Automatic event handling
@on_event(EventType.GENERATION_COMPLETED)
async def handle_generation_complete(event: Event):
    # Update metrics
    await analytics_repo.record_generation_complete(
        generation_id=event.data['generation_id'],
        success=event.data['success']
    )
    
    # Send notification
    if not event.data['success']:
        await send_failure_notification(event.data['user_id'])
```

## Service Layer Benefits

1. **Separation of Concerns**: API endpoints stay thin
2. **Reusability**: Services can be used from API, CLI, or tests
3. **Transaction Management**: Services handle complex transactions
4. **Event Coordination**: Services emit appropriate events
5. **Error Handling**: Centralized error handling and recovery

## Background Task Architecture

### Task Queues
- **generation**: High priority content generation
- **extraction**: Domain knowledge extraction
- **quality**: Quality checks
- **export**: File exports
- **maintenance**: Cleanup and maintenance

### Task Flow
1. API creates task in database
2. Service emits start event
3. Celery task picked up by worker
4. Task updates database status
5. Task emits completion event
6. Client polls or receives WebSocket update

## Event System Benefits

1. **Decoupling**: Components don't need direct references
2. **Extensibility**: Easy to add new event handlers
3. **Auditability**: All events can be logged
4. **Real-time Updates**: WebSocket integration ready
5. **Analytics**: Automatic metric collection

## Testing the Integration

### Unit Tests
```python
async def test_content_generation_service():
    # Mock dependencies
    mock_db = AsyncMock()
    mock_orchestrator = AsyncMock()
    
    service = ContentGenerationService(
        db=mock_db,
        orchestrator=mock_orchestrator
    )
    
    # Test generation start
    generation = await service.start_generation(...)
    assert generation.status == GenerationStatus.PENDING
```

### Integration Tests
```python
async def test_full_generation_flow():
    # Use test database
    async with get_test_db() as db:
        service = ContentGenerationService(db)
        
        # Start generation
        generation = await service.start_generation(...)
        
        # Process (normally done by Celery)
        await service.process_generation(generation.id)
        
        # Verify results
        assert generation.status == GenerationStatus.COMPLETED
```

## Configuration

### Environment Variables
```bash
# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Events
ENABLE_EVENT_BUS=true
EVENT_LOG_LEVEL=INFO

# Services
MAX_CONCURRENT_GENERATIONS=10
GENERATION_TIMEOUT=3600
```

### Running Workers
```bash
# Start Celery worker
celery -A certify_studio.integration.background worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A certify_studio.integration.background beat --loglevel=info

# Start Flower (monitoring)
celery -A certify_studio.integration.background flower
```

## Next Steps

1. **WebSocket Integration**: Real-time updates to frontend
2. **Workflow Engine**: Complex multi-step workflows
3. **Saga Pattern**: Distributed transaction management
4. **Event Sourcing**: Full audit trail
5. **CQRS**: Separate read/write models

## Summary

The integration layer is the glue that brings together:
- ✅ Database persistence
- ✅ Agent orchestration
- ✅ Background processing
- ✅ Event-driven architecture
- ✅ Clean API design

This provides a solid foundation for scaling and extending Certify Studio!
