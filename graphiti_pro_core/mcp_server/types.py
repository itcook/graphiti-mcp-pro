"""
Type definitions for MCP API responses.
"""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Any, TypedDict


class MCPStatus(Enum):
    """MCP Server status enumeration"""
    RUNNING = "running"
    STARTING = "starting"
    STOPPING = "stopping"
    STOPPED = "stopped"


class MCPStatusObserver(ABC):
    """Observer interface for MCP status changes"""

    @abstractmethod
    def on_change(self, status: MCPStatus) -> None:
        """Handle status change notification"""
        pass


# Type definitions for API responses
class ErrorResponse(TypedDict):
    error: str


class SuccessResponse(TypedDict):
    message: str


class NodeResult(TypedDict):
    uuid: str
    name: str
    summary: str
    labels: list[str]
    group_id: str
    created_at: str
    attributes: dict[str, Any]


class NodeSearchResponse(TypedDict):
    message: str
    nodes: list[NodeResult]


class FactSearchResponse(TypedDict):
    message: str
    facts: list[dict[str, Any]]


class EpisodeSearchResponse(TypedDict):
    message: str
    episodes: list[dict[str, Any]]


class StatusResponse(TypedDict):
    status: str
    message: str
