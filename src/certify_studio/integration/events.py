"""
Event-Driven Architecture

This module implements an event bus for decoupled communication between
components. Events are used to trigger workflows and update systems.
"""

from typing import Dict, Any, List, Callable, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
import asyncio
from enum import Enum
import json

from ..core.logging import get_logger

logger = get_logger(__name__)


class EventType(Enum):
    """Types of events in the system."""
    # Content generation events
    GENERATION_STARTED = "generation.started"
    GENERATION_COMPLETED = "generation.completed"
    GENERATION_FAILED = "generation.failed"
    GENERATION_PROGRESS = "generation.progress"
    
    # Quality events
    QUALITY_CHECK_STARTED = "quality.started"
    QUALITY_CHECK_COMPLETED = "quality.completed"
    QUALITY_ISSUE_FOUND = "quality.issue_found"
    
    # Domain extraction events
    EXTRACTION_STARTED = "extraction.started"
    EXTRACTION_COMPLETED = "extraction.completed"
    CONCEPT_DISCOVERED = "extraction.concept_discovered"
    
    # User events
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_UPGRADED = "user.upgraded"
    
    # Export events
    EXPORT_STARTED = "export.started"
    EXPORT_COMPLETED = "export.completed"
    EXPORT_FAILED = "export.failed"
    
    # Analytics events
    METRIC_RECORDED = "analytics.metric_recorded"
    THRESHOLD_EXCEEDED = "analytics.threshold_exceeded"


@dataclass
class Event:
    """Base event class."""
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'metadata': self.metadata
        }
        
    def to_json(self) -> str:
        """Convert event to JSON."""
        return json.dumps(self.to_dict())


# Specific event classes
@dataclass
class ContentGenerationStartedEvent(Event):
    """Event fired when content generation starts."""
    def __init__(self, generation_id: UUID, user_id: UUID, content_type: str):
        super().__init__(
            event_type=EventType.GENERATION_STARTED,
            data={
                'generation_id': str(generation_id),
                'user_id': str(user_id),
                'content_type': content_type
            }
        )


@dataclass
class ContentGenerationCompletedEvent(Event):
    """Event fired when content generation completes."""
    def __init__(self, generation_id: UUID, user_id: UUID, 
                 success: bool, content_pieces: int = 0, error: Optional[str] = None):
        super().__init__(
            event_type=EventType.GENERATION_COMPLETED,
            data={
                'generation_id': str(generation_id),
                'user_id': str(user_id),
                'success': success,
                'content_pieces': content_pieces,
                'error': error
            }
        )


@dataclass
class GenerationProgressEvent(Event):
    """Event fired to update generation progress."""
    def __init__(self, generation_id: UUID, progress: int, message: str):
        super().__init__(
            event_type=EventType.GENERATION_PROGRESS,
            data={
                'generation_id': str(generation_id),
                'progress': progress,
                'message': message
            }
        )


@dataclass
class QualityCheckCompletedEvent(Event):
    """Event fired when quality check completes."""
    def __init__(self, generation_id: UUID, check_id: UUID, 
                 passed: bool, score: float):
        super().__init__(
            event_type=EventType.QUALITY_CHECK_COMPLETED,
            data={
                'generation_id': str(generation_id),
                'check_id': str(check_id),
                'passed': passed,
                'score': score
            }
        )


@dataclass
class DomainExtractionCompletedEvent(Event):
    """Event fired when domain extraction completes."""
    def __init__(self, generation_id: UUID, concepts_count: int, 
                 relationships_count: int):
        super().__init__(
            event_type=EventType.EXTRACTION_COMPLETED,
            data={
                'generation_id': str(generation_id),
                'concepts_count': concepts_count,
                'relationships_count': relationships_count
            }
        )


@dataclass
class UserRegisteredEvent(Event):
    """Event fired when new user registers."""
    def __init__(self, user_id: UUID, email: str, username: str):
        super().__init__(
            event_type=EventType.USER_REGISTERED,
            data={
                'user_id': str(user_id),
                'email': email,
                'username': username
            }
        )


@dataclass
class MetricRecordedEvent(Event):
    """Event fired when metric is recorded."""
    def __init__(self, metric_name: str, value: float, 
                 dimensions: Optional[Dict[str, str]] = None):
        super().__init__(
            event_type=EventType.METRIC_RECORDED,
            data={
                'metric_name': metric_name,
                'value': value,
                'dimensions': dimensions or {}
            }
        )


class EventHandler:
    """Base class for event handlers."""
    
    def __init__(self):
        self.handlers: Dict[EventType, List[Callable]] = {}
        
    def register(self, event_type: EventType, handler: Callable):
        """Register a handler for an event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        
    def unregister(self, event_type: EventType, handler: Callable):
        """Unregister a handler."""
        if event_type in self.handlers:
            self.handlers[event_type].remove(handler)
            
    async def handle(self, event: Event):
        """Handle an event by calling all registered handlers."""
        if event.event_type in self.handlers:
            for handler in self.handlers[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")


class EventBus:
    """
    Central event bus for the application.
    
    Supports both sync and async handlers, event filtering,
    and can be extended to support external message queues.
    """
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._processor_task = None
        
    async def start(self):
        """Start the event processor."""
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        logger.info("Event bus started")
        
    async def stop(self):
        """Stop the event processor."""
        self._running = False
        if self._processor_task:
            await self._processor_task
        logger.info("Event bus stopped")
        
    async def emit(self, event: Event):
        """
        Emit an event to the bus.
        
        Args:
            event: Event to emit
        """
        await self._event_queue.put(event)
        logger.debug(f"Event emitted: {event.event_type.value}")
        
    def on(self, event_type: EventType, handler: Callable):
        """
        Register a handler for specific event type.
        
        Args:
            event_type: Type of event to handle
            handler: Handler function
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
            
        event_handler = EventHandler()
        event_handler.register(event_type, handler)
        self._handlers[event_type].append(event_handler)
        
        logger.debug(f"Handler registered for {event_type.value}")
        
    def on_all(self, handler: Callable):
        """
        Register a handler for all events.
        
        Args:
            handler: Handler function
        """
        event_handler = EventHandler()
        # Register for all event types
        for event_type in EventType:
            event_handler.register(event_type, handler)
        self._global_handlers.append(event_handler)
        
        logger.debug("Global handler registered")
        
    def off(self, event_type: EventType, handler: Callable):
        """
        Unregister a handler.
        
        Args:
            event_type: Event type
            handler: Handler to remove
        """
        if event_type in self._handlers:
            for event_handler in self._handlers[event_type]:
                event_handler.unregister(event_type, handler)
                
    async def _process_events(self):
        """
        Process events from the queue.
        """
        logger.info("Event processor started")
        
        while self._running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    self._event_queue.get(), 
                    timeout=1.0
                )
                
                # Process event
                await self._handle_event(event)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                
        logger.info("Event processor stopped")
        
    async def _handle_event(self, event: Event):
        """
        Handle a single event.
        
        Args:
            event: Event to handle
        """
        logger.debug(f"Handling event: {event.event_type.value}")
        
        # Call specific handlers
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                await handler.handle(event)
                
        # Call global handlers
        for handler in self._global_handlers:
            await handler.handle(event)
            

# Event handler decorators
def on_event(event_type: EventType):
    """
    Decorator to register a function as an event handler.
    
    Usage:
        @on_event(EventType.GENERATION_COMPLETED)
        async def handle_generation_complete(event: Event):
            print(f"Generation completed: {event.data['generation_id']}")
    """
    def decorator(func):
        # Will be registered when event bus is initialized
        func._event_type = event_type
        func._is_event_handler = True
        return func
    return decorator


# Default event handlers
class DefaultEventHandlers:
    """
    Default event handlers for common tasks.
    """
    
    @staticmethod
    async def log_event(event: Event):
        """
        Log all events.
        """
        logger.info(f"Event: {event.event_type.value} - {event.data}")
        
    @staticmethod
    async def record_metrics(event: Event):
        """
        Record metrics for certain events.
        """
        # Import here to avoid circular imports
        from ..database import get_db_session
        from ..database.repositories import AnalyticsRepository
        
        # Record metrics for specific events
        if event.event_type == EventType.GENERATION_COMPLETED:
            async with get_db_session() as db:
                repo = AnalyticsRepository(db.session)
                await repo.increment_metric(
                    "generations_completed",
                    dimensions={
                        "success": str(event.data.get('success', False))
                    }
                )
                await db.commit()
                
        elif event.event_type == EventType.USER_REGISTERED:
            async with get_db_session() as db:
                repo = AnalyticsRepository(db.session)
                await repo.increment_metric("users_registered")
                await db.commit()
                
    @staticmethod
    async def send_notifications(event: Event):
        """
        Send notifications for certain events.
        """
        # This could integrate with email, Slack, etc.
        if event.event_type == EventType.GENERATION_FAILED:
            logger.error(f"Generation failed: {event.data}")
            # TODO: Send email notification
            
        elif event.event_type == EventType.THRESHOLD_EXCEEDED:
            logger.warning(f"Threshold exceeded: {event.data}")
            # TODO: Send alert


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Get the global event bus instance.
    
    Returns:
        Global EventBus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def initialize_event_bus():
    """
    Initialize and start the global event bus.
    """
    bus = get_event_bus()
    
    # Register default handlers
    bus.on_all(DefaultEventHandlers.log_event)
    bus.on_all(DefaultEventHandlers.record_metrics)
    bus.on_all(DefaultEventHandlers.send_notifications)
    
    # Start the bus
    await bus.start()
    
    logger.info("Event bus initialized")
    

async def shutdown_event_bus():
    """
    Shutdown the global event bus.
    """
    bus = get_event_bus()
    await bus.stop()
    
    logger.info("Event bus shutdown")
