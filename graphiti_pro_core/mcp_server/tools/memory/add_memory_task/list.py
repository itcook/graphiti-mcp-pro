"""
Implementation of list_add_memory_tasks tool function.
"""

from ....types import ErrorResponse, SuccessResponse
from ..__task__ import TaskStatus, get_task_store


async def list_add_memory_tasks(
    group_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> SuccessResponse | ErrorResponse:
    """List add_memory tasks with optional filtering.

    Args:
        group_id (str, optional): Filter tasks by group_id
        status (str, optional): Filter tasks by status (queued, processing, completed, failed, cancelled)
        limit (int, optional): Maximum number of tasks to return (default: 50, max: 100)

    Returns:
        SuccessResponse with list of tasks or ErrorResponse if error occurs
    """
    task_store = get_task_store()

    try:
        # Validate limit
        if limit <= 0 or limit > 100:
            return ErrorResponse(error="Limit must be between 1 and 100")

        # Validate status if provided
        task_status = None
        if status:
            try:
                task_status = TaskStatus(status.lower())
            except ValueError:
                valid_statuses = [s.value for s in TaskStatus]
                return ErrorResponse(
                    error=f"Invalid status '{status}'. Valid statuses: {', '.join(valid_statuses)}"
                )

        # Get tasks from store
        tasks = await task_store.list_tasks(
            group_id=group_id,
            status=task_status,
            limit=limit,
        )

        # Convert tasks to response format
        task_list = []
        for task in tasks:
            task_data = {
                "task_id": task.task_id,
                "name": task.name,
                "group_id": task.group_id,
                "status": task.status.value,
                "progress": task.progress,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }

            # Add optional fields if they exist
            if task.started_at:
                task_data["started_at"] = task.started_at.isoformat()

            if task.completed_at:
                task_data["completed_at"] = task.completed_at.isoformat()

            if task.error_message:
                task_data["error_message"] = task.error_message

            task_list.append(task_data)

        # Build filter description for message
        filters: list[str] = []
        if group_id:
            filters.append(f"group_id='{group_id}'")
        if status:
            filters.append(f"status='{status}'")

        filter_desc = f" with filters: {', '.join(filters)}" if filters else ""

        return SuccessResponse(
            message=f"Found {len(task_list)} tasks{filter_desc}",
            data={
                "tasks": task_list,
                "total_returned": len(task_list),
                "limit": limit,
                "filters": {"group_id": group_id, "status": status},
            },
        )

    except Exception as e:
        return ErrorResponse(error=f"Error listing tasks: {str(e)}")

