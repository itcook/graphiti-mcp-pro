"""
Implementation of wait_for_add_memory_task tool function.
"""

import asyncio

from ....types import ErrorResponse, SuccessResponse
from ..__task__ import TaskStatus, get_task_store


async def wait_for_add_memory_task(
    task_id: str, timeout: int = 120
) -> SuccessResponse | ErrorResponse:
    """Wait for an add_memory task to complete with timeout.

    Args:
        task_id (str): The task ID returned by add_memory
        timeout (int, optional): Maximum time to wait in seconds (default: 120, max: 300)

    Returns:
        SuccessResponse with final task result or ErrorResponse if timeout/error occurs
    """
    task_store = get_task_store()

    try:
        # Validate timeout
        if timeout <= 0 or timeout > 300:
            return ErrorResponse(error="Timeout must be between 1 and 300 seconds")

        # Check if task exists
        task_info = await task_store.get_task(task_id)
        if task_info is None:
            return ErrorResponse(error=f"Task with ID '{task_id}' not found")

        # If task is already completed/failed/cancelled, return immediately
        if task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task_data = {
                "task_id": task_info.task_id,
                "name": task_info.name,
                "group_id": task_info.group_id,
                "status": task_info.status.value,
                "progress": task_info.progress,
                "created_at": task_info.created_at.isoformat(),
                "updated_at": task_info.updated_at.isoformat(),
            }
            if task_info.started_at:
                task_data["started_at"] = task_info.started_at.isoformat()
            if task_info.completed_at:
                task_data["completed_at"] = task_info.completed_at.isoformat()
            if task_info.error_message:
                task_data["error_message"] = task_info.error_message
            if task_info.result:
                task_data["result"] = task_info.result

            return SuccessResponse(
                message=f"Task '{task_id}' already {task_info.status.value}", data=task_data
            )

        # Wait for task completion with polling
        start_time = asyncio.get_event_loop().time()
        poll_interval = 1.0

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                return ErrorResponse(
                    error=f"Timeout waiting for task '{task_id}' to complete after {timeout} seconds"
                )

            current_task = await task_store.get_task(task_id)
            if current_task is None:
                return ErrorResponse(error=f"Task '{task_id}' was removed during wait")

            if current_task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                task_data = {
                    "task_id": current_task.task_id,
                    "name": current_task.name,
                    "group_id": current_task.group_id,
                    "status": current_task.status.value,
                    "progress": current_task.progress,
                    "created_at": current_task.created_at.isoformat(),
                    "updated_at": current_task.updated_at.isoformat(),
                    "wait_time": elapsed,
                }
                if current_task.started_at:
                    task_data["started_at"] = current_task.started_at.isoformat()
                if current_task.completed_at:
                    task_data["completed_at"] = current_task.completed_at.isoformat()
                if current_task.error_message:
                    task_data["error_message"] = current_task.error_message
                if current_task.result:
                    task_data["result"] = current_task.result

                return SuccessResponse(
                    message=f"Task '{task_id}' completed with status: {current_task.status.value}",
                    data=task_data,
                )

            await asyncio.sleep(poll_interval)

    except Exception as e:
        return ErrorResponse(error=f"Error waiting for task: {str(e)}")

