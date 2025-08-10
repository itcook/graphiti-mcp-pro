"""
Implementation of clear_graph tool function.
"""

from typing import cast
from graphiti_core import Graphiti
from graphiti_core.utils.maintenance.graph_data_operations import clear_data
from utils import logger

from ...types import ErrorResponse, SuccessResponse
from ....clients import get_graphiti_client

async def clear_graph() -> SuccessResponse | ErrorResponse:
    """Clear all data from the graph memory and rebuild indices."""
    graphiti_client = get_graphiti_client()

    if graphiti_client is None:
        return ErrorResponse(error='Graphiti client not initialized')

    try:
        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # clear_data is already imported at the top
        await clear_data(client.driver)
        await client.build_indices_and_constraints()
        return SuccessResponse(message='✅ Graph cleared successfully and indices rebuilt')
    except Exception as e:
        error_msg = str(e)
        logger.error(f'❌ Error clearing graph: {error_msg}')
        return ErrorResponse(error=f'Error clearing graph: {error_msg}')
