import threading
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .server import MCPServer

from .types import MCPStatus, MCPStatusObserver


class MCPStatusSubject:
    """MCP status subject class - uses observer pattern for status management"""

    def __init__(self):
        self._value: MCPStatus = MCPStatus.STOPPED
        self._observer: Optional[MCPStatusObserver] = None
        self._lock = threading.RLock()  # Thread-safe

    def attach(self, observer: MCPStatusObserver) -> None:
        """Attach observer"""
        with self._lock:
            self._observer = observer

    def detach(self) -> None:
        """Detach observer"""
        with self._lock:
            self._observer = None

    def notify(self) -> None:
        """Notify observer of status change"""
        with self._lock:
            if self._observer is not None:
                try:
                    self._observer.on_change(self._value)
                except Exception as e:
                    # Log error but don't raise to avoid breaking state management
                    import logging
                    logging.error(f"Error notifying status observer: {e}")

    @property
    def value(self) -> MCPStatus:
        """Get current status"""
        with self._lock:
            return self._value

    @value.setter
    def value(self, new_value: MCPStatus) -> None:
        """Set new status and notify observer"""
        with self._lock:
            if self._value != new_value:
                self._value = new_value
                self.notify()


# Global status instance
mcp_status = MCPStatusSubject()

# Global server instance
mcp_server: "MCPServer | None" = None


def set_mcp_server(server: "MCPServer") -> None:
    """Set MCP server instance."""
    global mcp_server
    mcp_server = server

def get_mcp_server() -> "MCPServer | None":
    """Get MCP server instance."""
    return mcp_server

def is_mcp_initialized() -> bool:
    """Check if initialized."""
    return mcp_server is not None

__all__ = [
    "mcp_status",
    "MCPStatusSubject",
    "set_mcp_server",
    "get_mcp_server",
    "is_mcp_initialized",
]
