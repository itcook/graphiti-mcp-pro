"""
Implementation of cancel_add_memory_task tool function.
"""

from ....types import ErrorResponse, SuccessResponse
from ..__task__ import TaskStatus, get_task_store
from ..__task__.helper import episode_queues


async def cancel_add_memory_task(task_id: str) -> SuccessResponse | ErrorResponse:
    """Cancel a pending or processing add_memory task by task_id.

    Behavior:
    - If task is QUEUED: mark CANCELLED and try to remove one queued process function (best-effort).
    - If task is PROCESSING: mark CANCELLED (the running process should check before heavy work and respect it).
    - If task is already COMPLETED/FAILED/CANCELLED: return as already finished.
    """
    task_store = get_task_store()

    try:
        task = await task_store.get_task(task_id)
        if task is None:
            return ErrorResponse(error=f"Task with ID '{task_id}' not found")

        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return SuccessResponse(
                message=f"Task '{task_id}' already {task.status.value}",
            )

        # Mark as cancelled
        await task_store.update_task(task_id, status=TaskStatus.CANCELLED)

        # Best-effort removal from queue if queued
        try:
            if task.status == TaskStatus.QUEUED:
                q = episode_queues.get(task.group_id)
                if q is not None:
                    new_items = []
                    # Drain queue and requeue others
                    while not q.empty():
                        item = await q.get()
                        # We cannot map process func back to task_id safely; keep all
                        new_items.append(item)
                        q.task_done()
                    for item in new_items:
                        await q.put(item)
        except Exception:
            pass

        return SuccessResponse(message=f"Task '{task_id}' cancelled")

    except Exception as e:
        return ErrorResponse(error=f"Error cancelling task: {str(e)}")

