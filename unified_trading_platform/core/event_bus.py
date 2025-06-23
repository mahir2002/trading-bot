#!/usr/bin/env python3
"""
🚌 Event Bus System
Central communication hub for all modules
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from .base_module import ModuleEvent, ModulePriority

@dataclass
class EventSubscription:
    """Event subscription information"""
    module_name: str
    event_type: str
    handler: Callable
    priority: ModulePriority = ModulePriority.NORMAL

class EventBus:
    """
    Central event bus for inter-module communication
    
    Handles event routing, queuing, and delivery with priority support
    """
    
    def __init__(self, max_queue_size: int = 10000):
        self.max_queue_size = max_queue_size
        self.logger = logging.getLogger("EventBus")
        
        # Event queues by priority
        self.event_queues = {
            ModulePriority.CRITICAL: deque(),
            ModulePriority.HIGH: deque(),
            ModulePriority.NORMAL: deque(), 
            ModulePriority.LOW: deque()
        }
        
        # Module subscriptions: event_type -> [EventSubscription]
        self.subscriptions = defaultdict(list)
        
        # Module references for direct delivery
        self.modules = {}  # module_name -> module_instance
        
        # Event processing state
        self.running = False
        self.processing_task = None
        self.event_stats = {
            'total_sent': 0,
            'total_delivered': 0,
            'total_failed': 0,
            'queue_full_drops': 0
        }
        
        # Rate limiting
        self.rate_limits = {}  # module_name -> (count, last_reset)
        self.rate_limit_window = 60  # seconds
        self.default_rate_limit = 1000  # events per minute
        
        # Event history for debugging
        self.event_history = deque(maxlen=1000)
        
        self.logger.info("Event Bus initialized")
    
    async def start(self):
        """Start the event bus processing"""
        if self.running:
            self.logger.warning("Event bus already running")
            return
            
        self.running = True
        self.processing_task = asyncio.create_task(self._process_events())
        self.logger.info("Event Bus started")
    
    async def stop(self):
        """Stop the event bus processing"""
        if not self.running:
            return
            
        self.running = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
                
        self.logger.info("Event Bus stopped")
    
    def register_module(self, module_name: str, module_instance):
        """Register a module with the event bus"""
        self.modules[module_name] = module_instance
        module_instance.event_bus = self
        self.logger.info(f"Module registered: {module_name}")
    
    def unregister_module(self, module_name: str):
        """Unregister a module from the event bus"""
        if module_name in self.modules:
            del self.modules[module_name]
            
        # Remove subscriptions for this module
        for event_type in list(self.subscriptions.keys()):
            self.subscriptions[event_type] = [
                sub for sub in self.subscriptions[event_type] 
                if sub.module_name != module_name
            ]
            
        self.logger.info(f"Module unregistered: {module_name}")
    
    def subscribe(self, module_name: str, event_type: str, handler: Callable, 
                  priority: ModulePriority = ModulePriority.NORMAL):
        """
        Subscribe a module to an event type
        
        Args:
            module_name: Name of the subscribing module
            event_type: Type of event to subscribe to
            handler: Handler function to call
            priority: Priority of this subscription
        """
        subscription = EventSubscription(
            module_name=module_name,
            event_type=event_type,
            handler=handler,
            priority=priority
        )
        
        self.subscriptions[event_type].append(subscription)
        
        # Sort by priority (higher priority first)
        self.subscriptions[event_type].sort(
            key=lambda x: x.priority.value
        )
        
        self.logger.debug(f"Module {module_name} subscribed to {event_type}")
    
    def unsubscribe(self, module_name: str, event_type: str):
        """Unsubscribe a module from an event type"""
        if event_type in self.subscriptions:
            self.subscriptions[event_type] = [
                sub for sub in self.subscriptions[event_type]
                if sub.module_name != module_name
            ]
            
        self.logger.debug(f"Module {module_name} unsubscribed from {event_type}")
    
    async def send_event(self, event: ModuleEvent) -> bool:
        """
        Send an event through the bus
        
        Args:
            event: ModuleEvent to send
            
        Returns:
            bool: True if event was queued successfully
        """
        # Check rate limiting
        if not self._check_rate_limit(event.source_module):
            self.logger.warning(f"Rate limit exceeded for module: {event.source_module}")
            return False
        
        # Add to appropriate priority queue
        priority_queue = self.event_queues[event.priority]
        
        if len(priority_queue) >= self.max_queue_size:
            self.event_stats['queue_full_drops'] += 1
            self.logger.warning(f"Event queue full, dropping event: {event.event_type}")
            return False
        
        priority_queue.append(event)
        self.event_stats['total_sent'] += 1
        
        # Add to history for debugging
        self.event_history.append({
            'timestamp': event.timestamp,
            'event_type': event.event_type,
            'source': event.source_module,
            'target': event.target_module,
            'priority': event.priority.value
        })
        
        self.logger.debug(f"Event queued: {event.event_type} from {event.source_module}")
        return True
    
    async def _process_events(self):
        """Main event processing loop"""
        while self.running:
            try:
                # Process events by priority
                event = self._get_next_event()
                
                if event:
                    await self._deliver_event(event)
                else:
                    # No events to process, small delay
                    await asyncio.sleep(0.01)
                    
            except Exception as e:
                self.logger.error(f"Error in event processing: {e}")
                await asyncio.sleep(0.1)
    
    def _get_next_event(self) -> Optional[ModuleEvent]:
        """Get the next event to process (by priority)"""
        # Check queues in priority order
        for priority in [ModulePriority.CRITICAL, ModulePriority.HIGH, 
                        ModulePriority.NORMAL, ModulePriority.LOW]:
            queue = self.event_queues[priority]
            if queue:
                return queue.popleft()
        
        return None
    
    async def _deliver_event(self, event: ModuleEvent):
        """
        Deliver an event to subscribed modules
        
        Args:
            event: ModuleEvent to deliver
        """
        try:
            # Get subscribers for this event type
            subscribers = self.subscriptions.get(event.event_type, [])
            
            if not subscribers:
                self.logger.debug(f"No subscribers for event: {event.event_type}")
                return
            
            # Filter by target module if specified
            if event.target_module:
                subscribers = [
                    sub for sub in subscribers 
                    if sub.module_name == event.target_module
                ]
            
            # Deliver to each subscriber
            delivery_tasks = []
            for subscription in subscribers:
                if subscription.module_name in self.modules:
                    module = self.modules[subscription.module_name]
                    task = asyncio.create_task(
                        module.handle_event(event)
                    )
                    delivery_tasks.append((subscription.module_name, task))
            
            # Wait for all deliveries to complete
            for module_name, task in delivery_tasks:
                try:
                    success = await asyncio.wait_for(task, timeout=5.0)
                    if success:
                        self.event_stats['total_delivered'] += 1
                    else:
                        self.event_stats['total_failed'] += 1
                        
                except asyncio.TimeoutError:
                    self.logger.warning(f"Event delivery timeout to module: {module_name}")
                    self.event_stats['total_failed'] += 1
                    
                except Exception as e:
                    self.logger.error(f"Event delivery failed to {module_name}: {e}")
                    self.event_stats['total_failed'] += 1
                    
        except Exception as e:
            self.logger.error(f"Error delivering event {event.event_type}: {e}")
            self.event_stats['total_failed'] += 1
    
    def _check_rate_limit(self, module_name: str) -> bool:
        """
        Check if module is within rate limits
        
        Args:
            module_name: Name of the module
            
        Returns:
            bool: True if within limits
        """
        now = time.time()
        
        if module_name not in self.rate_limits:
            self.rate_limits[module_name] = [1, now]
            return True
        
        count, last_reset = self.rate_limits[module_name]
        
        # Reset counter if window has passed
        if now - last_reset >= self.rate_limit_window:
            self.rate_limits[module_name] = [1, now]
            return True
        
        # Check if under limit
        if count < self.default_rate_limit:
            self.rate_limits[module_name][0] += 1
            return True
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        queue_sizes = {
            f"queue_{priority.value}": len(queue)
            for priority, queue in self.event_queues.items()
        }
        
        return {
            'running': self.running,
            'total_modules': len(self.modules),
            'total_subscriptions': sum(len(subs) for subs in self.subscriptions.values()),
            'queue_sizes': queue_sizes,
            'event_stats': self.event_stats.copy(),
            'rate_limits_active': len(self.rate_limits)
        }
    
    def get_module_stats(self, module_name: str) -> Dict[str, Any]:
        """Get statistics for a specific module"""
        if module_name not in self.modules:
            return {}
        
        module = self.modules[module_name]
        subscriptions = []
        
        for event_type, subs in self.subscriptions.items():
            for sub in subs:
                if sub.module_name == module_name:
                    subscriptions.append({
                        'event_type': event_type,
                        'priority': sub.priority.value
                    })
        
        return {
            'module_name': module_name,
            'status': module.status.value,
            'subscriptions': subscriptions,
            'metrics': module.get_metrics(),
            'rate_limit_status': self.rate_limits.get(module_name, [0, 0])
        }
    
    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent event history"""
        return list(self.event_history)[-limit:]
    
    def clear_queues(self):
        """Clear all event queues"""
        for queue in self.event_queues.values():
            queue.clear()
        self.logger.info("Event queues cleared")
    
    def __str__(self):
        return f"EventBus(modules={len(self.modules)}, running={self.running})" 