"""
Unit tests for event system.

Tests event bus, event handling, and event propagation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, call
from datetime import datetime
from uuid import uuid4

from certify_studio.integration.events import (
    EventBus, Event, EventType, EventHandler,
    ContentGenerationStartedEvent, ContentGenerationCompletedEvent,
    ContentGenerationFailedEvent, QualityCheckCompletedEvent,
    UserRegisteredEvent, ExportCompletedEvent
)
from certify_studio.database.models import ContentType, GenerationStatus


@pytest.mark.unit
class TestEventBus:
    """Test event bus functionality."""
    
    @pytest.fixture
    def event_bus(self):
        """Create event bus instance."""
        return EventBus()
    
    async def test_event_bus_initialization(self, event_bus):
        """Test event bus initialization."""
        await event_bus.start()
        
        assert event_bus._started is True
        assert len(event_bus._handlers) > 0  # Default handlers registered
        
        await event_bus.stop()
        assert event_bus._started is False
        
    async def test_register_handler(self, event_bus):
        """Test handler registration."""
        # Create mock handler
        handler = AsyncMock()
        
        # Register for specific event type
        event_bus.register(EventType.GENERATION_STARTED, handler)
        
        assert EventType.GENERATION_STARTED in event_bus._handlers
        assert handler in event_bus._handlers[EventType.GENERATION_STARTED]
        
        # Register multiple handlers for same event
        handler2 = AsyncMock()
        event_bus.register(EventType.GENERATION_STARTED, handler2)
        
        assert len(event_bus._handlers[EventType.GENERATION_STARTED]) == 2
        
    async def test_unregister_handler(self, event_bus):
        """Test handler unregistration."""
        handler = AsyncMock()
        event_bus.register(EventType.GENERATION_COMPLETED, handler)
        
        # Unregister
        event_bus.unregister(EventType.GENERATION_COMPLETED, handler)
        
        assert handler not in event_bus._handlers.get(EventType.GENERATION_COMPLETED, [])
        
    async def test_emit_event(self, event_bus):
        """Test event emission."""
        await event_bus.start()
        
        # Create handler
        handler = AsyncMock()
        event_bus.register(EventType.GENERATION_STARTED, handler)
        
        # Create event
        event = ContentGenerationStartedEvent(
            generation_id=uuid4(),
            user_id=uuid4(),
            content_type=ContentType.MINI_COURSE,
            title="Test Course"
        )
        
        # Emit event
        await event_bus.emit(EventType.GENERATION_STARTED, event)
        
        # Allow event processing
        await asyncio.sleep(0.1)
        
        # Verify handler called
        handler.assert_called_once()
        call_args = handler.call_args[0]
        assert isinstance(call_args[0], ContentGenerationStartedEvent)
        assert call_args[0].title == "Test Course"
        
    async def test_multiple_handlers_called(self, event_bus):
        """Test multiple handlers are called for same event."""
        await event_bus.start()
        
        # Create multiple handlers
        handlers = [AsyncMock() for _ in range(3)]
        for handler in handlers:
            event_bus.register(EventType.GENERATION_COMPLETED, handler)
        
        # Emit event
        event = ContentGenerationCompletedEvent(
            generation_id=uuid4(),
            user_id=uuid4(),
            content_type=ContentType.EXAM_PREP,
            duration=3600.0,
            quality_score=0.88
        )
        
        await event_bus.emit(EventType.GENERATION_COMPLETED, event)
        await asyncio.sleep(0.1)
        
        # All handlers should be called
        for handler in handlers:
            handler.assert_called_once()
            
    async def test_handler_error_handling(self, event_bus):
        """Test error handling in event handlers."""
        await event_bus.start()
        
        # Create failing handler
        failing_handler = AsyncMock(side_effect=Exception("Handler error"))
        
        # Create successful handler
        success_handler = AsyncMock()
        
        event_bus.register(EventType.GENERATION_FAILED, failing_handler)
        event_bus.register(EventType.GENERATION_FAILED, success_handler)
        
        # Emit event
        event = ContentGenerationFailedEvent(
            generation_id=uuid4(),
            user_id=uuid4(),
            error="Test error",
            stage="processing"
        )
        
        await event_bus.emit(EventType.GENERATION_FAILED, event)
        await asyncio.sleep(0.1)
        
        # Both handlers should be called despite error
        failing_handler.assert_called_once()
        success_handler.assert_called_once()
        
    async def test_event_decorator(self, event_bus):
        """Test event handler decorator."""
        # Track calls
        calls = []
        
        @event_bus.on(EventType.USER_REGISTERED)
        async def handle_user_registered(event: UserRegisteredEvent):
            calls.append(event)
        
        await event_bus.start()
        
        # Emit event
        event = UserRegisteredEvent(
            user_id=uuid4(),
            email="test@example.com",
            username="testuser"
        )
        
        await event_bus.emit(EventType.USER_REGISTERED, event)
        await asyncio.sleep(0.1)
        
        assert len(calls) == 1
        assert calls[0].email == "test@example.com"


@pytest.mark.unit
class TestEventTypes:
    """Test specific event types and their data."""
    
    def test_content_generation_started_event(self):
        """Test content generation started event."""
        event = ContentGenerationStartedEvent(
            generation_id=uuid4(),
            user_id=uuid4(),
            content_type=ContentType.FULL_CERTIFICATION,
            title="AWS Certification"
        )
        
        assert event.event_type == EventType.GENERATION_STARTED
        assert event.title == "AWS Certification"
        assert event.content_type == ContentType.FULL_CERTIFICATION
        assert event.timestamp is not None
        
    def test_content_generation_completed_event(self):
        """Test content generation completed event."""
        gen_id = uuid4()
        event = ContentGenerationCompletedEvent(
            generation_id=gen_id,
            user_id=uuid4(),
            content_type=ContentType.MINI_COURSE,
            duration=2400.0,
            quality_score=0.92
        )
        
        assert event.event_type == EventType.GENERATION_COMPLETED
        assert event.generation_id == gen_id
        assert event.duration == 2400.0
        assert event.quality_score == 0.92
        
    def test_quality_check_completed_event(self):
        """Test quality check completed event."""
        event = QualityCheckCompletedEvent(
            generation_id=uuid4(),
            check_id=uuid4(),
            passed=True,
            overall_score=0.88,
            metrics={
                "accuracy": 0.92,
                "pedagogy": 0.86,
                "engagement": 0.85
            }
        )
        
        assert event.event_type == EventType.QUALITY_CHECK_COMPLETED
        assert event.passed is True
        assert event.overall_score == 0.88
        assert event.metrics["accuracy"] == 0.92
        
    def test_export_completed_event(self):
        """Test export completed event."""
        event = ExportCompletedEvent(
            export_id=uuid4(),
            generation_id=uuid4(),
            format="pdf",
            file_path="/exports/course.pdf",
            file_size=2048000  # 2MB
        )
        
        assert event.event_type == EventType.EXPORT_COMPLETED
        assert event.format == "pdf"
        assert event.file_size == 2048000
        
    def test_event_serialization(self):
        """Test event can be serialized to dict."""
        event = UserRegisteredEvent(
            user_id=uuid4(),
            email="user@example.com",
            username="newuser"
        )
        
        data = event.to_dict()
        
        assert "event_type" in data
        assert "timestamp" in data
        assert "data" in data
        assert data["data"]["email"] == "user@example.com"


@pytest.mark.unit
class TestDefaultHandlers:
    """Test default event handlers."""
    
    @pytest.fixture
    def mock_logger(self, mocker):
        """Mock logger."""
        return mocker.patch("certify_studio.integration.events.logger")
    
    @pytest.fixture
    def mock_metrics(self, mocker):
        """Mock metrics collector."""
        return mocker.patch("certify_studio.integration.events.metrics")
    
    async def test_log_handler(self, event_bus, mock_logger):
        """Test default logging handler."""
        from certify_studio.integration.events import log_event
        
        # Register log handler
        event_bus.register(EventType.GENERATION_STARTED, log_event)
        
        # Emit event
        event = ContentGenerationStartedEvent(
            generation_id=uuid4(),
            user_id=uuid4(),
            content_type=ContentType.QUICK_REVIEW,
            title="Quick Review"
        )
        
        await log_event(event)
        
        # Verify logging
        mock_logger.info.assert_called()
        log_message = mock_logger.info.call_args[0][0]
        assert "GENERATION_STARTED" in log_message
        
    async def test_metrics_handler(self, event_bus, mock_metrics):
        """Test default metrics handler."""
        from certify_studio.integration.events import track_metrics
        
        # Emit different events
        events = [
            ContentGenerationStartedEvent(
                generation_id=uuid4(),
                user_id=uuid4(),
                content_type=ContentType.MINI_COURSE,
                title="Test"
            ),
            ContentGenerationCompletedEvent(
                generation_id=uuid4(),
                user_id=uuid4(),
                content_type=ContentType.MINI_COURSE,
                duration=1800.0,
                quality_score=0.85
            )
        ]
        
        for event in events:
            await track_metrics(event)
        
        # Verify metrics tracked
        assert mock_metrics.increment.called
        assert mock_metrics.gauge.called
        
    async def test_notification_handler(self, event_bus, mocker):
        """Test notification handler."""
        mock_notifier = mocker.patch("certify_studio.integration.events.notification_service")
        
        from certify_studio.integration.events import send_notifications
        
        # Test generation completed notification
        event = ContentGenerationCompletedEvent(
            generation_id=uuid4(),
            user_id=uuid4(),
            content_type=ContentType.FULL_CERTIFICATION,
            duration=3600.0,
            quality_score=0.92
        )
        
        await send_notifications(event)
        
        # Verify notification sent
        mock_notifier.send.assert_called_once()
        notification = mock_notifier.send.call_args[0][0]
        assert "completed" in notification.message.lower()


@pytest.mark.unit
class TestEventHandlerPatterns:
    """Test common event handler patterns."""
    
    async def test_event_chain(self, event_bus):
        """Test chaining events (one event triggers another)."""
        await event_bus.start()
        
        # Handler that emits another event
        @event_bus.on(EventType.GENERATION_COMPLETED)
        async def trigger_quality_check(event: ContentGenerationCompletedEvent):
            # Trigger quality check
            quality_event = Event(
                event_type=EventType.QUALITY_CHECK_STARTED,
                data={"generation_id": event.generation_id}
            )
            await event_bus.emit(EventType.QUALITY_CHECK_STARTED, quality_event)
        
        # Track quality check events
        quality_checks = []
        
        @event_bus.on(EventType.QUALITY_CHECK_STARTED)
        async def track_quality_check(event: Event):
            quality_checks.append(event)
        
        # Emit initial event
        event = ContentGenerationCompletedEvent(
            generation_id=uuid4(),
            user_id=uuid4(),
            content_type=ContentType.MINI_COURSE,
            duration=1200.0,
            quality_score=0.8
        )
        
        await event_bus.emit(EventType.GENERATION_COMPLETED, event)
        await asyncio.sleep(0.2)  # Allow chain to complete
        
        # Verify chain executed
        assert len(quality_checks) == 1
        assert quality_checks[0].data["generation_id"] == event.generation_id
        
    async def test_conditional_handler(self, event_bus):
        """Test conditional event handling."""
        await event_bus.start()
        
        high_quality_generations = []
        
        @event_bus.on(EventType.GENERATION_COMPLETED)
        async def track_high_quality(event: ContentGenerationCompletedEvent):
            # Only track high quality generations
            if event.quality_score >= 0.9:
                high_quality_generations.append(event)
        
        # Emit events with different quality scores
        events = [
            ContentGenerationCompletedEvent(
                generation_id=uuid4(),
                user_id=uuid4(),
                content_type=ContentType.MINI_COURSE,
                duration=1200.0,
                quality_score=score
            )
            for score in [0.85, 0.92, 0.88, 0.95]
        ]
        
        for event in events:
            await event_bus.emit(EventType.GENERATION_COMPLETED, event)
        
        await asyncio.sleep(0.1)
        
        # Only high quality should be tracked
        assert len(high_quality_generations) == 2
        assert all(e.quality_score >= 0.9 for e in high_quality_generations)
        
    async def test_aggregating_handler(self, event_bus):
        """Test handler that aggregates multiple events."""
        await event_bus.start()
        
        class EventAggregator:
            def __init__(self):
                self.events = []
                self.summary = {}
            
            async def handle_event(self, event: ContentGenerationCompletedEvent):
                self.events.append(event)
                
                # Update summary
                content_type = event.content_type.value
                if content_type not in self.summary:
                    self.summary[content_type] = {
                        "count": 0,
                        "total_duration": 0,
                        "total_quality": 0
                    }
                
                self.summary[content_type]["count"] += 1
                self.summary[content_type]["total_duration"] += event.duration
                self.summary[content_type]["total_quality"] += event.quality_score
        
        aggregator = EventAggregator()
        event_bus.register(EventType.GENERATION_COMPLETED, aggregator.handle_event)
        
        # Emit multiple events
        for i in range(5):
            event = ContentGenerationCompletedEvent(
                generation_id=uuid4(),
                user_id=uuid4(),
                content_type=ContentType.MINI_COURSE if i % 2 == 0 else ContentType.EXAM_PREP,
                duration=1200.0 + i * 300,
                quality_score=0.8 + i * 0.02
            )
            await event_bus.emit(EventType.GENERATION_COMPLETED, event)
        
        await asyncio.sleep(0.1)
        
        # Check aggregation
        assert len(aggregator.events) == 5
        assert ContentType.MINI_COURSE.value in aggregator.summary
        assert ContentType.EXAM_PREP.value in aggregator.summary
        assert aggregator.summary[ContentType.MINI_COURSE.value]["count"] == 3
        assert aggregator.summary[ContentType.EXAM_PREP.value]["count"] == 2


@pytest.mark.unit
class TestEventIntegration:
    """Test event integration with services."""
    
    async def test_service_event_emission(self, event_bus, db, test_user):
        """Test services emit correct events."""
        from certify_studio.integration.services import ContentGenerationService
        
        # Create service with event bus
        service = ContentGenerationService(db, event_bus, None)
        
        # Track events
        emitted_events = []
        
        @event_bus.on(EventType.GENERATION_STARTED)
        async def track_event(event):
            emitted_events.append(event)
        
        await event_bus.start()
        
        # Mock file path
        with pytest.raises(Exception):  # Will fail due to missing orchestrator
            await service.start_generation(
                user=test_user,
                file_path="/test.pdf",
                file_name="test.pdf",
                title="Test Course",
                content_type=ContentType.MINI_COURSE,
                settings={}
            )
        
        await asyncio.sleep(0.1)
        
        # Event should still be emitted before error
        assert len(emitted_events) > 0
        assert isinstance(emitted_events[0], ContentGenerationStartedEvent)
