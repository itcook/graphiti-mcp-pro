"""
Task status management data models for memory operations.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel


class TaskStatus(Enum):
    """Enumeration of possible task statuses."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskInfo(BaseModel):
    """Information about a memory task."""
    task_id: str
    name: str
    group_id: str
    status: TaskStatus
    progress: int = 0  # 0-100
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskResponse(BaseModel):
    """Response model for task operations."""
    task_id: str
    status: TaskStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class BatchTaskResponse(BaseModel):
    """Response model for batch task operations."""
    task_ids: list[str]
    total_tasks: int
    queued_tasks: int
    message: str
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
