"""
Unified log management module.

Provides standardized logging configuration, specific library log level control, and easy-to-use logging interface.
"""

import logging
import sys
import asyncio
from typing import Optional, Dict, Any
from enum import Enum


class AsyncLogHandler:
    """Simple async log handler for management backend integration"""

    def __init__(self):
        self.log_queue = asyncio.Queue(maxsize=1000)
        self.worker_task = None

    async def start(self):
        """Start background worker task"""
        # Check if worker task is already running
        if self.worker_task is not None and not self.worker_task.done():
            return  # Worker already running, skip

        self.worker_task = asyncio.create_task(self._process_log_queue())

    def enqueue_log(self, level: str, message: str, source: str):
        """Add log entry to queue (non-blocking)"""
        try:
            log_entry = {
                'level': level,
                'message': message,
                'source': source
            }
            self.log_queue.put_nowait(log_entry)
        except asyncio.QueueFull:
            # Silently drop logs when queue is full
            pass

    async def _process_log_queue(self):
        """Process log queue in background"""
        while True:
            try:
                # Wait for log entry
                log_entry = await self.log_queue.get()

                # Try to send to management backend
                await self._try_send_to_backend(log_entry)

                # Mark task as done
                self.log_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception:
                # Silently handle exceptions, continue processing
                pass

    async def _try_send_to_backend(self, log_entry: dict):
        """Try to send log to management backend"""
        try:
            # Dynamic import to avoid circular dependency
            from utils.manager_backend_ctx import available_manager_backend

            # Use existing health check mechanism
            async with available_manager_backend() as backend:
                await backend.create_log(
                    level=log_entry['level'],
                    message=log_entry['message'],
                    source=log_entry['source']
                )

        except Exception:
            # Silently handle all exceptions (including backend unavailable)
            # This ensures core service is not affected
            pass


class BackendLogHandler(logging.Handler):
    """Backend log handler for sending logs to management backend"""

    def __init__(self, async_handler: AsyncLogHandler):
        super().__init__()
        self.async_handler = async_handler

    def emit(self, record: logging.LogRecord):
        """Handle log record"""
        try:
            # Level mapping
            level_mapping = {
                'DEBUG': 'debug',
                'INFO': 'info',
                'WARNING': 'warn',
                'ERROR': 'error',
                'CRITICAL': 'error'
            }

            backend_level = level_mapping.get(record.levelname, 'info')
            message = self.format(record)

            # Create source with filename:lineno format
            source = f"{record.filename}:{record.lineno}"

            # Add to queue without checking backend status
            self.async_handler.enqueue_log(backend_level, message, source)

        except Exception:
            # Silently handle exceptions
            pass


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LoggerManager:
    """Log manager providing unified logging configuration and management functionality."""

    # Default log format
    DEFAULT_FORMAT = '[%(asctime)s][%(levelname)s][%(name)s]: %(message)s'

    # Simplified format (for development environment)
    SIMPLE_FORMAT = '[%(levelname)s]: %(message)s'

    # Detailed format (for production environment)
    DETAILED_FORMAT = '[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)d]: %(message)s'

    _configured = False
    _loggers: Dict[str, logging.Logger] = {}
    _async_handler: Optional[AsyncLogHandler] = None
    _handler_initialized = False

    @classmethod
    def setup_logging(
        cls,
        level: LogLevel = LogLevel.INFO,
        format_string: Optional[str] = None,
        stream: Optional[Any] = None,
        force_reconfigure: bool = False
    ) -> None:
        """
        Setup global logging configuration.

        Args:
            level: Log level
            format_string: Log format string
            stream: Output stream, defaults to sys.stderr
            force_reconfigure: Whether to force reconfiguration
        """
        if cls._configured and not force_reconfigure:
            return

        # Set default values
        if format_string is None:
            format_string = cls.DETAILED_FORMAT
        if stream is None:
            stream = sys.stderr

        # Configure root logger
        logging.basicConfig(
            level=level.value,
            format=format_string,
            stream=stream,
            force=force_reconfigure
        )

        cls._configured = True

    @classmethod
    def _ensure_async_handler(cls):
        """Ensure async handler is initialized"""
        if not cls._handler_initialized:
            cls._async_handler = AsyncLogHandler()
            cls._handler_initialized = True

    @classmethod
    def get_logger(
        cls,
        name: Optional[str] = None,
        level: Optional[LogLevel] = None
    ) -> logging.Logger:
        """
        Get logger instance.

        Args:
            name: Logger name, defaults to caller module's name
            level: Log level, if specified overrides global level

        Returns:
            Configured logger instance
        """
        # Ensure async handler is initialized
        cls._ensure_async_handler()

        if name is None:
            # Get caller's module name
            import inspect
            frame = inspect.currentframe()
            if frame and frame.f_back:
                name = frame.f_back.f_globals.get('__name__', 'unknown')
            else:
                name = 'unknown'

        # If already created, return directly
        if name in cls._loggers:
            logger_instance = cls._loggers[name]
        else:
            logger_instance = logging.getLogger(name)
            cls._loggers[name] = logger_instance

        # Set specific level
        if level is not None:
            logger_instance.setLevel(level.value)
            
        
        return logger_instance

    @classmethod
    def set_library_log_level(
        cls,
        library_prefix: str,
        level: LogLevel
    ) -> None:
        """
        Set specific library log level.

        Args:
            library_prefix: Library name prefix (e.g., 'neo4j', 'urllib3')
            level: Log level to set
        """
        for logger_name in logging.root.manager.loggerDict:
            if logger_name.startswith(library_prefix):
                logging.getLogger(logger_name).setLevel(level.value)

    @classmethod
    def setup_global_backend_handler(cls):
        """Setup backend handler for root logger to capture all third-party logs"""
        # Ensure async handler is initialized
        cls._ensure_async_handler()

        if cls._async_handler:
            root_logger = logging.getLogger()  # Get root logger

            # Check if backend handler already exists
            has_backend_handler = any(
                isinstance(h, BackendLogHandler) for h in root_logger.handlers
            )

            if not has_backend_handler:
                backend_handler = BackendLogHandler(cls._async_handler)
                root_logger.addHandler(backend_handler)
                # Use the default logger to avoid circular dependency
                import sys
                print("✅ Backend handler added to root logger for third-party dependencies", file=sys.stderr)

    @classmethod
    def reset_configuration(cls) -> None:
        """Reset logging configuration."""
        cls._configured = False
        cls._loggers.clear()
        

def setup_logging(
    level: LogLevel = LogLevel.INFO,
    format_string: Optional[str] = None,
    stream: Optional[Any] = None,
    force_reconfigure: bool = False
) -> None:
    """
    Convenience function to setup global logging configuration.

    Args:
        level: Log level
        format_string: Log format string
        stream: Output stream, defaults to sys.stderr
        force_reconfigure: Whether to force reconfiguration
    """
    LoggerManager.setup_logging(level, format_string, stream, force_reconfigure)

def get_logger(name: Optional[str] = None, level: Optional[LogLevel] = None) -> logging.Logger:
    """
    Convenience function to get logger.

    Args:
        name: Logger name
        level: Log level

    Returns:
        Logger instance
    """
    return LoggerManager.get_logger(name, level)

def set_library_log_level(library_prefix: str, level: LogLevel) -> None:
    """
    Convenience function to set specific library log level.

    Args:
        library_prefix: Library name prefix
        level: Log level
    """
    LoggerManager.set_library_log_level(library_prefix, level)


async def initialize_async_logging():
    """Initialize async logging system for management backend integration"""
    # Ensure async handler is created and started
    LoggerManager._ensure_async_handler()
    if LoggerManager._async_handler:
        await LoggerManager._async_handler.start()

    # Setup global backend handler for third-party dependencies
    LoggerManager.setup_global_backend_handler()


# Create default logger instance (maintain backward compatibility)
logger = get_logger()