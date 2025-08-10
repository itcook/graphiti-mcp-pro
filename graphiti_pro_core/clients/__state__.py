"""
State management module - manages global variables and application state.

This module is responsible for managing global state shared by all tool functions, primarily Graphiti client instances.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graphiti_core import Graphiti    

# Global variables - will be set by GraphitiClient
graphiti_client: "Graphiti | None" = None

# State management functions
def set_graphiti_client(client: "Graphiti") -> None:
    """Set Graphiti client instance."""
    global graphiti_client
    graphiti_client = client

def get_graphiti_client() -> "Graphiti | None":
    """Get Graphiti client instance."""
    return graphiti_client

def is_graphiti_initialized() -> bool:
    """Check if initialized."""
    return graphiti_client is not None

# Export content
__all__ = [
    # Global variables
    "set_graphiti_client",
    "get_graphiti_client",
    "is_graphiti_initialized",
]
