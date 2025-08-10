"""
MCP Settings
"""
from pydantic import Field, BaseModel
from config import config_manager

class TaskSetting(BaseModel):
    # Task management configuration
    store_max_size: int = Field(default=1000, description="Maximum number of tasks to keep in memory")
    store_ttl: int = Field(default=3600, description="Time-to-live for completed/failed tasks in seconds")
    cleanup_interval: int = Field(default=300, description="Interval for periodic task cleanup in seconds")
    max_concurrent: int = Field(default=10, description="Maximum number of concurrent task processing")
    processing_timeout: int = Field(default=300, description="Timeout for individual task processing in seconds")
    max_workers_per_group: int = Field(default=5, description="Maximum number of workers per group_id for parallel processing")

task_setting: TaskSetting = TaskSetting()

# Field(default="default", description="Default group ID for memory operations")
default_group_id: str = "default"

# Field(default=True, description="Enable custom entity extraction")
use_custom_entities: bool = True

default_host: str = "0.0.0.0"


def get_entity_types():
    """Get entity types."""
    from .entities import ENTITY_TYPES
    return ENTITY_TYPES

async def get_enable_sync_return() -> bool:
    """Get whether synchronous return is enabled."""
    data = await config_manager.get_config(['enable_sync_return'])
    return data.get('enable_sync_return', False)