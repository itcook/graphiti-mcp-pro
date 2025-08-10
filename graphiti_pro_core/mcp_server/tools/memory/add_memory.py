"""
Implementation of add_memory tool function.
"""

import asyncio
from typing import cast
from datetime import datetime, timezone
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from utils import logger, EpisodeUsageContext

from .__task__ import (
    TaskStatus,
    get_task_store,
    episode_queues,
    queue_workers
)
from .__task__.helper import start_worker_for_group, get_active_worker_count

from ...settings import (
    get_entity_types,
    default_group_id,
    use_custom_entities,
    get_enable_sync_return
)
from ...types import ErrorResponse, SuccessResponse

from ....clients import get_graphiti_client

async def add_memory(
    name: str,
    episode_body: str,
    group_id: str | None = None,
    source: str = 'text',
    source_description: str = '',
    uuid: str | None = None,
) -> SuccessResponse | ErrorResponse:
    """Add an episode to memory. This is the primary way to add information to the graph.

    This function returns immediately and processes the episode addition in the background.
    Episodes for the same group_id are processed sequentially to avoid race conditions.

    Args:
        name (str): Name of the episode
        episode_body (str): The content of the episode to persist to memory. When source='json', this must be a
                           properly escaped JSON string, not a raw Python dictionary. The JSON data will be
                           automatically processed to extract entities and relationships.
        group_id (str, optional): A unique ID for this graph. If not provided, uses the default group_id from CLI
                                 or a generated one.
        source (str, optional): Source type, must be one of:
                               - 'text': For plain text content (default)
                               - 'json': For structured data
                               - 'message': For conversation-style content
        source_description (str, optional): Description of the source
        uuid (str, optional): Optional UUID for the episode

    Examples:
        # Adding plain text content
        add_memory(
            name="Company News",
            episode_body="Acme Corp announced a new product line today.",
            source="text",
            source_description="news article",
            group_id="some_arbitrary_string"
        )

        # Adding structured JSON data
        # NOTE: episode_body must be a properly escaped JSON string. Note the triple backslashes
        add_memory(
            name="Customer Profile",
            episode_body="{\\\"company\\\": {\\\"name\\\": \\\"Acme Technologies\\\"}, \\\"products\\\": [{\\\"id\\\": \\\"P001\\\", \\\"name\\\": \\\"CloudSync\\\"}, {\\\"id\\\": \\\"P002\\\", \\\"name\\\": \\\"DataMiner\\\"}]}",
            source="json",
            source_description="CRM data"
        )

        # Adding message-style content
        add_memory(
            name="Customer Conversation",
            episode_body="user: What's your return policy?\nassistant: You can return items within 30 days.",
            source="message",
            source_description="chat transcript",
            group_id="some_arbitrary_string"
        )

    Notes:
        When using source='json':
        - The JSON must be a properly escaped string, not a raw Python dictionary
        - The JSON will be automatically processed to extract entities and relationships
        - Complex nested structures are supported (arrays, nested objects, mixed data types), but keep nesting to a minimum
        - Entities will be created from appropriate JSON properties
        - Relationships between entities will be established based on the JSON structure
    """
    global episode_queues, queue_workers

    graphiti_client = get_graphiti_client()
    task_store = get_task_store()

    if graphiti_client is None:
        return ErrorResponse(error='Graphiti client not initialized')

    try:
        # Check if sync return is enabled
        enable_sync_return = await get_enable_sync_return()

        # Create task and get task ID
        task_id = await task_store.create_task(name=name, group_id=group_id or 'default')
        # Map string source to EpisodeType enum
        source_type = EpisodeType.text
        if source.lower() == 'message':
            source_type = EpisodeType.message
        elif source.lower() == 'json':
            source_type = EpisodeType.json

        # Use the provided group_id or fall back to the default from config
        effective_group_id = group_id if group_id is not None else default_group_id

        # Cast group_id to str to satisfy type checker
        # The Graphiti client expects a str for group_id, not Optional[str]
        group_id_str = str(effective_group_id) if effective_group_id is not None else ''

        # We've already checked that graphiti_client is not None above
        # This assert statement helps type checkers understand that graphiti_client is defined
        assert graphiti_client is not None, 'graphiti_client should not be None here'

        # Use cast to help the type checker understand that graphiti_client is not None
        client = cast(Graphiti, graphiti_client)

        # Define the episode processing function with task status updates
        async def process_episode():
            try:
                # Check cancellation before processing
                current = await task_store.get_task(task_id)
                if current and current.status == TaskStatus.CANCELLED:
                    logger.info(f"⚠️ Task '{task_id}' was cancelled before processing")
                    return

                # Set episode context for usage collection
                async with EpisodeUsageContext(name):
                    # Update task status to processing
                    await task_store.update_task(task_id, status=TaskStatus.PROCESSING, progress=0)
                    logger.info(f"⏳ Processing queued episode '{name}' for group_id: {group_id_str}")

                    # Update progress: entity extraction phase
                    await task_store.update_task(task_id, progress=10)

                    # Use all entity types if use_custom_entities is enabled, otherwise use empty dict
                    entity_types = get_entity_types() if use_custom_entities else {}

                    # Update progress: graph building phase
                    # await task_store.update_task(task_id, progress=50)

                    # Update progress: database persistence phase
                    await task_store.update_task(task_id, progress=20)

                    await client.add_episode(
                        name=name,
                        episode_body=episode_body,
                        source=source_type,
                        source_description=source_description,
                        group_id=group_id_str,  # Using the string version of group_id
                        uuid=uuid,
                        reference_time=datetime.now(timezone.utc),
                        entity_types=entity_types,
                    )

                # Update task status to completed
                await task_store.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100,
                    result={"message": "Episode added successfully"}
                )

                logger.info(f"✅ Episode '{name}' added successfully")
                logger.info(f"✅ Episode '{name}' processed successfully")

            except Exception as e:
                error_msg = str(e)

                # Update task status to failed
                await task_store.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    error_message=error_msg
                )

                logger.error(
                    f"❌ Error processing episode '{name}' for group_id {group_id_str}: {error_msg}"
                )

                # Re-raise exception for sync mode
                if enable_sync_return:
                    raise

        if enable_sync_return:
            # Synchronous processing - execute immediately and wait for completion
            try:
                # Set episode context for usage collection in sync mode too
                async with EpisodeUsageContext(name):
                    await process_episode()
                return SuccessResponse(
                    message=f"Episode '{name}' added successfully",
                    data={
                        "task_id": task_id,
                        "status": "completed"
                    }
                )
            except Exception as e:
                error_msg = str(e)
                logger.error(f'❌ Error processing episode synchronously: {error_msg}')
                return ErrorResponse(error=f'Error processing episode: {error_msg}')
        else:
            # Asynchronous processing - use queue system
            # Initialize queue for this group_id if it doesn't exist
            if group_id_str not in episode_queues:
                episode_queues[group_id_str] = asyncio.Queue()

            # Add the episode processing function to the queue
            await episode_queues[group_id_str].put(process_episode)

            # Start workers for this queue if needed (up to MAX_WORKERS_PER_GROUP)
            active_workers = get_active_worker_count(group_id_str)
            queue_size = episode_queues[group_id_str].qsize()

            # Start additional workers if queue is growing and we have capacity
            if queue_size > active_workers and active_workers == 0:
                # Always start at least one worker
                start_worker_for_group(group_id_str)
            elif queue_size > active_workers * 2:
                # Start additional workers if queue is backing up
                start_worker_for_group(group_id_str)

            # Return immediately with success message including task ID
            return SuccessResponse(
                message=f"Episode '{name}' queued for processing (task_id: {task_id}, position: {queue_size}, workers: {get_active_worker_count(group_id_str)})",
                data={
                    "task_id": task_id,
                    "status": "queued",
                    "queue_position": queue_size,
                    "active_workers": get_active_worker_count(group_id_str)
                }
            )
    except Exception as e:
        error_msg = str(e)
        logger.error(f'❌ Error queuing episode task: {error_msg}')
        return ErrorResponse(error=f'Error queuing episode task: {error_msg}')
