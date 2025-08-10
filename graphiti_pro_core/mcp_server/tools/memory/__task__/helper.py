"""
Task management helper functions for memory operations.
"""

import asyncio
from utils import logger

# Dictionary to store queues for each group_id
# Each queue is a list of tasks to be processed with limited concurrency
episode_queues: dict[str, asyncio.Queue] = {}
# Dictionary to track worker tasks for each group_id (now supports multiple workers per group)
queue_workers: dict[str, list[asyncio.Task]] = {}

# Global task store instance for tracking memory operation tasks
task_store = None

# Global semaphore for controlling concurrent task processing
processing_semaphore: asyncio.Semaphore | None = None

# Background tasks list for managing periodic cleanup tasks (module-level variable)
background_tasks: list[asyncio.Task] = []
# Registry for episode queue worker tasks (deprecated, use queue_workers instead)
worker_tasks: dict[str, asyncio.Task] = {}

# Maximum number of concurrent workers per group_id (will be updated from config)
MAX_WORKERS_PER_GROUP = 5



def initialize_task_store(max_size: int = 10000, ttl: int = 3600):
    """Initialize the global task store."""
    global task_store
    if task_store is None:
        # Delayed import to avoid circular references
        from .store import MemoryTaskStore
        task_store = MemoryTaskStore(max_size=max_size, ttl=ttl)
        logger.info(f"✅ Task store initialized with max_size={max_size}, ttl={ttl}")
    return task_store


def initialize_processing_semaphore(max_concurrent: int = 10) -> asyncio.Semaphore:
    """Initialize the global processing semaphore."""
    global processing_semaphore
    if processing_semaphore is None:
        processing_semaphore = asyncio.Semaphore(max_concurrent)
        logger.info(f"✅ Processing semaphore initialized with max_concurrent={max_concurrent}")
    return processing_semaphore


def get_processing_semaphore() -> asyncio.Semaphore:
    """Get the global processing semaphore."""
    global processing_semaphore
    if processing_semaphore is None:
        processing_semaphore = initialize_processing_semaphore()
    return processing_semaphore


def get_task_store():
    """Get the global task store instance."""
    global task_store
    if task_store is None:
        task_store = initialize_task_store()
    return task_store


async def cleanup_expired_tasks():
    """Periodic cleanup of expired tasks."""
    if task_store:
        removed_count = await task_store.cleanup_expired_tasks()
        if removed_count > 0:
            logger.info(f"🧹 Cleaned up {removed_count} expired tasks")


async def process_episode_queue(group_id: str, worker_id: int):
    """Process episodes for a specific group_id with limited concurrency.

    This function runs as a long-lived task that processes episodes
    from the queue with multiple workers per group_id.

    Args:
        group_id: The group ID to process episodes for
        worker_id: Unique identifier for this worker within the group
    """
    global queue_workers

    logger.info(f'⏳ Starting episode queue worker {worker_id} for group_id: {group_id}')

    try:
        while True:
            # Get the next episode processing function from the queue
            # This will wait if the queue is empty
            process_func = await episode_queues[group_id].get()

            try:
                # Use semaphore to control concurrent processing
                semaphore = get_processing_semaphore()
                async with semaphore:
                    await asyncio.wait_for(process_func(), timeout=300)
            except asyncio.TimeoutError:
                logger.error(f'⏰ Episode processing timeout for group_id {group_id}, worker {worker_id}')
            except Exception as e:
                logger.error(f'❌ Error processing queued episode for group_id {group_id}, worker {worker_id}: {str(e)}')
            finally:
                # Mark the task as done regardless of success/failure
                episode_queues[group_id].task_done()
    except asyncio.CancelledError:
        logger.info(f'⚠️ Episode queue worker {worker_id} for group_id {group_id} was cancelled')
    except Exception as e:
        logger.error(f'❌ Unexpected error in queue worker {worker_id} for group_id {group_id}: {str(e)}')
    finally:
        logger.info(f'⚠️ Stopped episode queue worker {worker_id} for group_id: {group_id}')


def get_active_worker_count(group_id: str) -> int:
    """Get the number of active workers for a specific group_id."""
    if group_id not in queue_workers:
        return 0

    # Filter out completed/cancelled tasks
    active_workers = [task for task in queue_workers[group_id] if not task.done()]
    queue_workers[group_id] = active_workers  # Clean up completed tasks

    return len(active_workers)


def start_worker_for_group(group_id: str) -> bool:
    """Start a new worker for the specified group_id if under the limit.

    Returns:
        True if a new worker was started, False if already at limit
    """
    active_count = get_active_worker_count(group_id)

    if active_count >= MAX_WORKERS_PER_GROUP:
        return False

    # Initialize workers list if not exists
    if group_id not in queue_workers:
        queue_workers[group_id] = []

    # Create new worker with unique ID
    worker_id = active_count + 1
    worker_task = asyncio.create_task(process_episode_queue(group_id, worker_id))
    queue_workers[group_id].append(worker_task)

    logger.info(f'✅ Started new worker {worker_id} for group_id {group_id} (total: {active_count + 1})')
    return True


async def start_periodic_cleanup(interval: int = 300):
    """Start periodic cleanup of expired tasks.

    Args:
        interval: Cleanup interval in seconds (default: 5 minutes)
    """
    logger.info(f"🧹 Starting periodic task cleanup with {interval}s interval")

    while True:
        try:
            await asyncio.sleep(interval)
            await cleanup_expired_tasks()
        except asyncio.CancelledError:
            logger.info("⚠️ Periodic cleanup task was cancelled")
            break
        except Exception as e:
            logger.error(f"❌ Error in periodic cleanup: {str(e)}")


def initialize_task_manager():
    """Initialize task management system and start background tasks."""
    global MAX_WORKERS_PER_GROUP
    try:
        # Initialize task store with MCP configuration
        from ....settings import task_setting
        initialize_task_store(
            max_size=task_setting.store_max_size,
            ttl=task_setting.store_ttl
        )

        # Initialize processing semaphore
        initialize_processing_semaphore(task_setting.max_concurrent)

        # Update max workers per group from configuration
        MAX_WORKERS_PER_GROUP = task_setting.max_workers_per_group

        # Start periodic cleanup task and track it
        cleanup_task = asyncio.create_task(start_periodic_cleanup(task_setting.cleanup_interval))
        background_tasks.append(cleanup_task)

    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize task management: {str(e)}")
        # Initialize with defaults
        initialize_task_store()
        initialize_processing_semaphore()
        cleanup_task = asyncio.create_task(start_periodic_cleanup())
        background_tasks.append(cleanup_task)


async def cleanup_task_manager():
    """Clean up background tasks managed by task manager."""
    try:
        # Clean up background tasks
        for task in background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        background_tasks.clear()

        # Clean up episode queue worker tasks (legacy)
        for group_id, task in list(worker_tasks.items()):
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        worker_tasks.clear()

        # Clean up new multi-worker tasks
        for group_id, tasks in list(queue_workers.items()):
            for task in tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
        queue_workers.clear()

        logger.info("🧹 Background and worker tasks cleaned up")
    except Exception as e:
        logger.error(f"❌ Error during task cleanup: {e}")
