"""
Implementation of search_memory_facts tool function.
"""

# from utils import (
#     cast,
#     Graphiti,
#     ErrorResponse,
#     FactSearchResponse,
#     format_fact_result,
#     get_graphiti_client,
#     logger,
# )

from typing import cast
from graphiti_core import Graphiti
from utils import logger

from ..utils import format_fact_result
from ...types import ErrorResponse, FactSearchResponse
from ...settings import default_group_id
from ....clients import get_graphiti_client

async def search_memory_facts(
    query: str,
    group_ids: list[str] | None = None,
    max_facts: int = 10,
    center_node_uuid: str | None = None,
) -> FactSearchResponse | ErrorResponse:
    """Search the graph memory for relevant facts.

    Args:
        query: The search query
        group_ids: Optional list of group IDs to filter results
        max_facts: Maximum number of facts to return (default: 10)
        center_node_uuid: Optional UUID of a node to center the search around
    """
    graphiti_client = get_graphiti_client()

    if graphiti_client is None:
        return ErrorResponse(error='Graphiti client not initialized')

    try:
        # Validate max_facts parameter
        if max_facts <= 0:
            return ErrorResponse(error='max_facts must be a positive integer')

        # Use the provided group_ids or fall back to the default from config if none provided
        effective_group_ids = (
            group_ids if group_ids is not None else [default_group_id]
        )

        # We've already checked that graphiti_client is not None above
        assert graphiti_client is not None

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        relevant_edges = await client.search(
            group_ids=effective_group_ids,
            query=query,
            num_results=max_facts,
            center_node_uuid=center_node_uuid,
        )

        if not relevant_edges:
            return FactSearchResponse(message='No relevant facts found', facts=[])

        facts = [format_fact_result(edge) for edge in relevant_edges]
        return FactSearchResponse(message='Facts retrieved successfully', facts=facts)
    except Exception as e:
        error_msg = str(e)
        logger.error(f'❌ Error searching facts: {error_msg}')
        return ErrorResponse(error=f'Error searching facts: {error_msg}')
