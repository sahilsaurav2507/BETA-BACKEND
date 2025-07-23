"""
Round Robin Registration Manager
===============================

This module implements a round-robin registration system with a 10-person
concurrent limit to prevent system overload and ensure optimal performance.

Features:
- Maximum 10 concurrent registrations
- Round-robin scheduling for fair processing
- Queue management for overflow requests
- Automatic cleanup of completed registrations
- Thread-safe operations
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
from collections import deque

logger = logging.getLogger(__name__)

class RegistrationStatus(Enum):
    """Registration request status."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class RegistrationRequest:
    """Registration request data structure."""
    request_id: str
    user_data: Dict[str, Any]
    callback: Callable
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: RegistrationStatus = RegistrationStatus.QUEUED
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class RoundRobinRegistrationManager:
    """
    Round-robin registration manager with 10-person concurrent limit.
    
    This manager ensures that only 10 registrations are processed simultaneously,
    with additional requests queued and processed in round-robin fashion.
    """
    
    def __init__(self, max_concurrent: int = 10, timeout_seconds: int = 300):
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds
        
        # Thread-safe data structures
        self.lock = threading.RLock()
        self.active_registrations: Dict[str, RegistrationRequest] = {}
        self.registration_queue: deque = deque()
        self.completed_registrations: Dict[str, RegistrationRequest] = {}
        
        # Round-robin tracking
        self.current_slot = 0
        self.processing_slots: List[Optional[str]] = [None] * max_concurrent
        
        # Background cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "completed_requests": 0,
            "failed_requests": 0,
            "timeout_requests": 0,
            "current_queue_size": 0,
            "average_processing_time": 0.0
        }
        
        logger.info(f"Round-robin registration manager initialized with {max_concurrent} concurrent slots")
    
    def submit_registration(self, user_data: Dict[str, Any], callback: Callable) -> str:
        """
        Submit a registration request for processing.
        
        Args:
            user_data: User registration data
            callback: Function to call for actual registration processing
            
        Returns:
            str: Request ID for tracking
        """
        request_id = str(uuid.uuid4())
        
        request = RegistrationRequest(
            request_id=request_id,
            user_data=user_data,
            callback=callback,
            created_at=datetime.utcnow()
        )
        
        with self.lock:
            self.stats["total_requests"] += 1
            
            # Try to assign to an available slot immediately
            if len(self.active_registrations) < self.max_concurrent:
                self._assign_to_slot(request)
                logger.info(f"Registration {request_id} assigned to immediate processing")
            else:
                # Add to queue
                self.registration_queue.append(request)
                self.stats["current_queue_size"] = len(self.registration_queue)
                logger.info(f"Registration {request_id} queued (queue size: {len(self.registration_queue)})")
        
        return request_id
    
    def _assign_to_slot(self, request: RegistrationRequest):
        """Assign a registration request to an available processing slot."""
        # Find next available slot using round-robin
        for i in range(self.max_concurrent):
            slot_index = (self.current_slot + i) % self.max_concurrent
            if self.processing_slots[slot_index] is None:
                self.processing_slots[slot_index] = request.request_id
                self.current_slot = (slot_index + 1) % self.max_concurrent
                break
        
        # Mark as active and start processing
        request.status = RegistrationStatus.PROCESSING
        request.started_at = datetime.utcnow()
        self.active_registrations[request.request_id] = request
        
        # Start processing in a separate thread
        processing_thread = threading.Thread(
            target=self._process_registration,
            args=(request,),
            daemon=True
        )
        processing_thread.start()
    
    def _process_registration(self, request: RegistrationRequest):
        """Process a registration request."""
        try:
            logger.info(f"Starting registration processing for {request.request_id}")
            
            # Call the actual registration function
            result = request.callback(request.user_data)
            
            # Mark as completed
            with self.lock:
                request.status = RegistrationStatus.COMPLETED
                request.completed_at = datetime.utcnow()
                
                # Update statistics
                processing_time = (request.completed_at - request.started_at).total_seconds()
                self._update_average_processing_time(processing_time)
                self.stats["completed_requests"] += 1
                
                # Move to completed and free up slot
                self._complete_registration(request)
                
            logger.info(f"Registration {request.request_id} completed successfully in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Registration {request.request_id} failed: {e}")
            
            with self.lock:
                request.error_message = str(e)
                request.retry_count += 1
                
                # Retry if under limit
                if request.retry_count <= request.max_retries:
                    logger.info(f"Retrying registration {request.request_id} (attempt {request.retry_count})")
                    # Add back to queue for retry
                    self.registration_queue.appendleft(request)
                    request.status = RegistrationStatus.QUEUED
                else:
                    # Mark as failed
                    request.status = RegistrationStatus.FAILED
                    request.completed_at = datetime.utcnow()
                    self.stats["failed_requests"] += 1
                    
                # Free up slot
                self._complete_registration(request)
    
    def _complete_registration(self, request: RegistrationRequest):
        """Complete a registration and free up its slot."""
        # Remove from active registrations
        if request.request_id in self.active_registrations:
            del self.active_registrations[request.request_id]
        
        # Free up processing slot
        for i, slot_id in enumerate(self.processing_slots):
            if slot_id == request.request_id:
                self.processing_slots[i] = None
                break
        
        # Move to completed registrations
        self.completed_registrations[request.request_id] = request
        
        # Process next item in queue
        if self.registration_queue:
            next_request = self.registration_queue.popleft()
            self.stats["current_queue_size"] = len(self.registration_queue)
            self._assign_to_slot(next_request)
            logger.info(f"Assigned queued registration {next_request.request_id} to processing")
    
    def _update_average_processing_time(self, new_time: float):
        """Update the rolling average processing time."""
        completed = self.stats["completed_requests"]
        if completed == 1:
            self.stats["average_processing_time"] = new_time
        else:
            # Rolling average
            current_avg = self.stats["average_processing_time"]
            self.stats["average_processing_time"] = (current_avg * (completed - 1) + new_time) / completed
    
    def _cleanup_worker(self):
        """Background worker to clean up old completed registrations."""
        while True:
            try:
                time.sleep(60)  # Run every minute
                
                with self.lock:
                    cutoff_time = datetime.utcnow() - timedelta(hours=1)  # Keep for 1 hour
                    
                    # Clean up old completed registrations
                    to_remove = []
                    for request_id, request in self.completed_registrations.items():
                        if request.completed_at and request.completed_at < cutoff_time:
                            to_remove.append(request_id)
                    
                    for request_id in to_remove:
                        del self.completed_registrations[request_id]
                    
                    if to_remove:
                        logger.debug(f"Cleaned up {len(to_remove)} old registration records")
                    
                    # Check for timeouts in active registrations
                    timeout_cutoff = datetime.utcnow() - timedelta(seconds=self.timeout_seconds)
                    timeout_requests = []
                    
                    for request_id, request in self.active_registrations.items():
                        if request.started_at and request.started_at < timeout_cutoff:
                            timeout_requests.append(request)
                    
                    # Handle timeouts
                    for request in timeout_requests:
                        logger.warning(f"Registration {request.request_id} timed out")
                        request.status = RegistrationStatus.TIMEOUT
                        request.completed_at = datetime.utcnow()
                        self.stats["timeout_requests"] += 1
                        self._complete_registration(request)
                        
            except Exception as e:
                logger.error(f"Error in registration cleanup worker: {e}")
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a registration request."""
        with self.lock:
            # Check active registrations
            if request_id in self.active_registrations:
                request = self.active_registrations[request_id]
                return {
                    "request_id": request_id,
                    "status": request.status.value,
                    "created_at": request.created_at.isoformat(),
                    "started_at": request.started_at.isoformat() if request.started_at else None,
                    "error_message": request.error_message,
                    "retry_count": request.retry_count
                }
            
            # Check completed registrations
            if request_id in self.completed_registrations:
                request = self.completed_registrations[request_id]
                return {
                    "request_id": request_id,
                    "status": request.status.value,
                    "created_at": request.created_at.isoformat(),
                    "started_at": request.started_at.isoformat() if request.started_at else None,
                    "completed_at": request.completed_at.isoformat() if request.completed_at else None,
                    "error_message": request.error_message,
                    "retry_count": request.retry_count
                }
            
            # Check queue
            for request in self.registration_queue:
                if request.request_id == request_id:
                    return {
                        "request_id": request_id,
                        "status": request.status.value,
                        "created_at": request.created_at.isoformat(),
                        "queue_position": list(self.registration_queue).index(request) + 1
                    }
            
            return None
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics."""
        with self.lock:
            return {
                **self.stats,
                "active_registrations": len(self.active_registrations),
                "available_slots": self.max_concurrent - len(self.active_registrations),
                "processing_slots": [slot is not None for slot in self.processing_slots]
            }

# Global registration manager instance
registration_manager = RoundRobinRegistrationManager()
