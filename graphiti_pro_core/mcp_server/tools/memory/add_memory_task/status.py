"""
Implementation of get_add_memory_task_status tool function.
"""

from ....types import ErrorResponse, SuccessResponse
from ..__task__ import get_task_store


async def get_add_memory_task_status(task_id: str) -> SuccessResponse | ErrorResponse:
    """Get the status of an add_memory task.

    Args:
        task_id (str): The task ID returned by add_memory

    Returns:
        SuccessResponse with task information or ErrorResponse if task not found
    """
    task_store = get_task_store()

    try:
        task_info = await task_store.get_task(task_id)

        if task_info is None:
            return ErrorResponse(error=f"Task with ID '{task_id}' not found")

        # Convert TaskInfo to dictionary for response
        task_data = {
            "task_id": task_info.task_id,
            "name": task_info.name,
            "group_id": task_info.group_id,
            "status": task_info.status.value,
            "progress": task_info.progress,
            "created_at": task_info.created_at.isoformat(),
            "updated_at": task_info.updated_at.isoformat(),
        }

        # Add optional fields if they exist
        if task_info.started_at:
            task_data["started_at"] = task_info.started_at.isoformat()

        if task_info.completed_at:
            task_data["completed_at"] = task_info.completed_at.isoformat()

        if task_info.error_message:
            task_data["error_message"] = task_info.error_message

        if task_info.result:
            task_data["result"] = task_info.result

        return SuccessResponse(
            message=f"Task '{task_id}' status: {task_info.status.value}",
            data=task_data,
        )

    except Exception as e:
        return ErrorResponse(error=f"Error retrieving task status: {str(e)}")

