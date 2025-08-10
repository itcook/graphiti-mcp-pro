"""
Memory-based task storage manager for tracking memory operation tasks.
"""

import asyncio
import time
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import uuid4

from .models import TaskInfo, TaskStatus


class MemoryTaskStore:
    """Memory-based task storage with LRU eviction and TTL support."""
    
    def __init__(self, max_size: int = 10000, ttl: int = 3600):
        """
        Initialize the task store.
        
        Args:
            max_size: Maximum number of tasks to keep in memory
            ttl: Time-to-live for completed/failed tasks in seconds
        """
        self.tasks: OrderedDict[str, TaskInfo] = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
        self._lock = asyncio.Lock()
    
    async def create_task(self, name: str, group_id: str) -> str:
        """
        Create a new task and return its ID.
        
        Args:
            name: Name of the episode/task
            group_id: Group ID for the task
            
        Returns:
            Generated task ID
        """
        async with self._lock:
            task_id = str(uuid4())
            now = datetime.now(timezone.utc)
            
            task_info = TaskInfo(
                task_id=task_id,
                name=name,
                group_id=group_id,
                status=TaskStatus.QUEUED,
                progress=0,
                created_at=now,
                updated_at=now
            )
            
            self.tasks[task_id] = task_info
            self._enforce_size_limit()
            
            return task_id
    
    async def update_task(self, task_id: str, **updates) -> bool:
        """
        Update task information.
        
        Args:
            task_id: Task ID to update
            **updates: Fields to update
            
        Returns:
            True if task was found and updated, False otherwise
        """
        async with self._lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            now = datetime.now(timezone.utc)
            
            # Update allowed fields
            if 'status' in updates:
                task.status = TaskStatus(updates['status'])
                if task.status == TaskStatus.PROCESSING and not task.started_at:
                    task.started_at = now
                elif task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    task.completed_at = now
            
            if 'progress' in updates:
                task.progress = max(0, min(100, updates['progress']))
            
            if 'error_message' in updates:
                task.error_message = updates['error_message']
            
            if 'result' in updates:
                task.result = updates['result']
            
            task.updated_at = now
            
            # Move to end (most recently used)
            self.tasks.move_to_end(task_id)
            
            return True
    
    async def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """
        Get task information by ID.
        
        Args:
            task_id: Task ID to retrieve
            
        Returns:
            TaskInfo if found, None otherwise
        """
        async with self._lock:
            if task_id in self.tasks:
                # Move to end (most recently used)
                self.tasks.move_to_end(task_id)
                return self.tasks[task_id]
            return None
    
    async def list_tasks(
        self, 
        group_id: Optional[str] = None, 
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[TaskInfo]:
        """
        List tasks with optional filtering.
        
        Args:
            group_id: Filter by group ID
            status: Filter by status
            limit: Maximum number of tasks to return
            
        Returns:
            List of matching tasks
        """
        async with self._lock:
            tasks = []
            count = 0
            
            # Iterate in reverse order (most recent first)
            for task in reversed(self.tasks.values()):
                if count >= limit:
                    break
                
                if group_id and task.group_id != group_id:
                    continue
                
                if status and task.status != status:
                    continue
                
                tasks.append(task)
                count += 1
            
            return tasks
    
    async def cleanup_expired_tasks(self) -> int:
        """
        Remove expired completed/failed tasks.
        
        Returns:
            Number of tasks removed
        """
        async with self._lock:
            current_time = time.time()
            expired_tasks = []
            
            for task_id, task in self.tasks.items():
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    if task.completed_at:
                        task_age = current_time - task.completed_at.timestamp()
                        if task_age > self.ttl:
                            expired_tasks.append(task_id)
            
            for task_id in expired_tasks:
                del self.tasks[task_id]
            
            return len(expired_tasks)
    
    def _enforce_size_limit(self):
        """Remove oldest tasks if size limit is exceeded."""
        while len(self.tasks) > self.max_size:
            # Remove oldest task (first in OrderedDict)
            oldest_task_id = next(iter(self.tasks))
            del self.tasks[oldest_task_id]
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Dictionary with storage stats
        """
        async with self._lock:
            status_counts = {}
            for task in self.tasks.values():
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "total_tasks": len(self.tasks),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "status_counts": status_counts
            }
