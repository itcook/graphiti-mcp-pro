"""
Utility module package.

Provides common utility functions such as logging management and parameter parsing.
"""

# Export logging related functionality
from .logger import (
    LoggerManager,
    LogLevel,
    setup_logging,
    set_library_log_level,
    get_logger,
    logger,  # Default logger
    initialize_async_logging,
)

from .manager_backend_ctx import (
    available_manager_backend,
)

from .usage_collector import (
    usage_collector,
    EpisodeUsageContext,
    get_current_episode_name
)

from .is_ import (
    is_in_docker,
    is_in_kubernetes,
)


__all__ = [
    "LoggerManager",
    "LogLevel",
    "setup_logging",
    "set_library_log_level",
    "get_logger",
    "logger",
    "initialize_async_logging",
    "get_settings",
    "available_manager_backend",
    "usage_collector",
    "EpisodeUsageContext",
    "get_current_episode_name",
    "is_in_docker",
    "is_in_kubernetes",
]
