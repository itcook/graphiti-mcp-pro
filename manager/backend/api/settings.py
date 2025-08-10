from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

from graphiti_pro_core import GraphitiMCPServer, MCPStatus, mcp_status
from config import config_manager

from ..models import SettingUpdate, SettingResponse
from ..database import get_session, get_setting, update_setting
from ..scheduler import log_cleanup_scheduler

router = APIRouter(prefix="/settings", tags=["settings"])

def _setting_to_response(setting):
    """Dynamically convert Setting object to response model"""
    from config.constants import CONFIG_METADATA

    response_data = {'id': setting.id}

    for key in CONFIG_METADATA.keys():
        # Use key name to get value regardless of sensitivity
        # Sensitive fields will be automatically decrypted through properties
        response_data[key] = getattr(setting, key)

    return SettingResponse(**response_data)


@router.get("/", response_model=SettingResponse)
async def get_current_setting(session: Session = Depends(get_session)):
    """Get current settings"""
    try:
        setting = get_setting()
        return _setting_to_response(setting)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/", response_model=SettingResponse)
async def update_current_setting(
    setting_update: SettingUpdate, #pyright: ignore
    session: Session = Depends(get_session)
):
    """Update current settings"""
    try:
        # Only update non-None fields
        update_data = setting_update.model_dump(exclude_unset=True, exclude_none=True)

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Check if clean_logs_at_hour is being updated
        clean_logs_at_hour_updated = 'clean_logs_at_hour' in update_data
        old_clean_hour = None

        if clean_logs_at_hour_updated:
            # Get current setting to compare
            current_setting = get_setting()
            old_clean_hour = current_setting.clean_logs_at_hour

        updated_setting = update_setting(update_data)

        # Reschedule log cleanup job if clean_logs_at_hour was updated
        if clean_logs_at_hour_updated and old_clean_hour != updated_setting.clean_logs_at_hour:
            try:
                log_cleanup_scheduler.reschedule_cleanup_job(updated_setting.clean_logs_at_hour)
                print(f"Log cleanup job rescheduled from {old_clean_hour}:00 to {updated_setting.clean_logs_at_hour}:00")
            except Exception as scheduler_error:
                print(f"Warning: Failed to reschedule log cleanup job: {scheduler_error}")
                # Don't fail the entire update if scheduler fails
                
        if mcp_status.value is MCPStatus.RUNNING:
            try:
                await GraphitiMCPServer.restart()
            except Exception as e:
                print(f"Warning: Failed to restart MCP server: {e}")
                
        elif mcp_status.value is MCPStatus.STOPPED:
            try:
                if not GraphitiMCPServer.is_initialized():
                    await GraphitiMCPServer.initialize()
                await GraphitiMCPServer.start()
            except Exception as e:
                print(f"Warning: Failed to start MCP server: {e}")

        return _setting_to_response(updated_setting)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# @router.get("/scheduler-status")
# async def get_scheduler_status():
#     """Get log cleanup scheduler status"""
#     try:
#         next_run_time = log_cleanup_scheduler.get_next_run_time()

#         return {
#             "scheduler_running": log_cleanup_scheduler.scheduler.running if log_cleanup_scheduler.scheduler else False,
#             "next_cleanup_time": next_run_time.isoformat() if next_run_time else None,
#             "job_id": log_cleanup_scheduler.job_id,
#             "initialized": log_cleanup_scheduler._initialized
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error getting scheduler status: {str(e)}")


# @router.post("/trigger-cleanup")
# async def trigger_manual_cleanup():
#     """Manually trigger log cleanup (for testing)"""
#     try:
#         log_cleanup_scheduler.trigger_cleanup_now()
#         return {"message": "Manual log cleanup triggered successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error triggering manual cleanup: {str(e)}")
