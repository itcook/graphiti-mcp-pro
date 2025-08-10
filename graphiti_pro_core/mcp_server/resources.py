"""
MCP resource functions for Graphiti operations.
"""

from typing import cast
from mcp.server.fastmcp.resources import FunctionResource

from graphiti_core import Graphiti

from .types import StatusResponse
from ..clients import get_graphiti_client

from utils import logger


async def get_status() -> StatusResponse:
    """Get the status of the Graphiti MCP server and Neo4j connection."""
    graphiti_client = get_graphiti_client()

    if graphiti_client is None:
        return StatusResponse(status='error', message='Graphiti client not initialized')

    try:
        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Test database connection
        await client.driver.client.verify_connectivity()  # type: ignore

        return StatusResponse(
            status='ok', message='✅ Graphiti MCP server is running and connected to Neo4j'
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f'❌ Error checking Neo4j connection: {error_msg}')
        return StatusResponse(
            status='error',
            message=f'❌ Graphiti MCP server is running but Neo4j connection failed: {error_msg}',
        )

get_status_resource = FunctionResource.from_function(fn=get_status, uri="http://graphiti/status")