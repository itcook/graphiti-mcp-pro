import uuid
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, func, and_, or_
from pydantic import BaseModel
from ..models import LogEntry, LogEntryCreate, LogEntryResponse
from ..database import get_session

router = APIRouter(prefix="/logs", tags=["logs"])


class PaginatedLogEntries(BaseModel):
    """Paginated log entries response model"""
    items: List[LogEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


def _log_entry_to_response(log_entry: LogEntry) -> LogEntryResponse:
    """Convert LogEntry object to response model"""
    return LogEntryResponse(
        id=log_entry.id,
        timestamp=log_entry.timestamp.isoformat(),
        level=log_entry.level,
        message=log_entry.message,
        source=log_entry.source
    )


@router.get("/history", response_model=PaginatedLogEntries)
async def get_log_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    level: Optional[str] = Query(None, description="Log level filter"),
    search: Optional[str] = Query(None, description="Search keyword (search in source and message)"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    session: Session = Depends(get_session)
):
    """Get historical logs with pagination"""
    query = select(LogEntry)
    
    # Add level filtering
    if level:
        query = query.where(LogEntry.level == level)
    
    # Add time range filtering
    if start_time:
        query = query.where(LogEntry.timestamp >= start_time)
    if end_time:
        # Use < (end_time + 1 day) to include the entire end date and avoid precision issues
        end_time_next_day = end_time + timedelta(days=1)
        query = query.where(LogEntry.timestamp < end_time_next_day)
    
    # Add search filtering
    if search:
        search_condition = or_(
            LogEntry.message.contains(search),
            LogEntry.source.contains(search)
        )
        query = query.where(search_condition)
    
    # Order by time descending
    query = query.order_by(LogEntry.timestamp.desc())
    
    # Calculate total count
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()
    
    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    log_entries = session.exec(query).all()
    
    # Convert to response model
    items = [_log_entry_to_response(entry) for entry in log_entries]
    
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedLogEntries(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/", response_model=LogEntryResponse)
async def create_log_entry(
    log_entry: LogEntryCreate,
    session: Session = Depends(get_session)
):
    """Create new log entry"""
    # Generate UUID as primary key
    log_id = str(uuid.uuid4())
    
    # Create log entry
    db_log_entry = LogEntry(
        id=log_id,
        level=log_entry.level,
        message=log_entry.message,
        source=log_entry.source,
        timestamp=datetime.now()
    )
    
    session.add(db_log_entry)
    session.commit()
    session.refresh(db_log_entry)
    
    return _log_entry_to_response(db_log_entry)


@router.get("/levels")
async def get_log_levels():
    """Get available log levels"""
    return {
        "levels": ["info", "warn", "error", "debug"]
    }


@router.delete("/cleanup")
async def cleanup_old_logs(
    days: Optional[int] = Query(None, description="Delete logs from how many days ago, use system config if not provided"),
    session: Session = Depends(get_session)
):
    """Clean up expired logs"""
    if days is None:
        # Get save days from system settings
        try:
            from ..database import get_setting
        except ImportError:
            from manager.backend.database import get_setting
        
        setting = get_setting()
        days = setting.log_save_days
    
    # Calculate cutoff time
    cutoff_time = datetime.now() - timedelta(days=days)
    
    # Delete expired logs
    delete_query = select(LogEntry).where(LogEntry.timestamp < cutoff_time)
    old_logs = session.exec(delete_query).all()
    
    deleted_count = len(old_logs)
    for log in old_logs:
        session.delete(log)
    
    session.commit()
    
    return {
        "deleted_count": deleted_count,
        "cutoff_time": cutoff_time.isoformat(),
        "days": days
    }


async def log_stream_generator(
    level_filter: Optional[str] = None,
    search_filter: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """Real-time log stream generator"""
    last_check_time = datetime.now()

    while True:
        try:
            # Get database session
            from ..database import engine
            with Session(engine) as session:
                # Query new logs
                query = select(LogEntry).where(LogEntry.timestamp > last_check_time)

                # Add level filtering
                if level_filter:
                    query = query.where(LogEntry.level == level_filter)

                # Add search filtering
                if search_filter:
                    search_condition = or_(
                        LogEntry.message.contains(search_filter),
                        LogEntry.source.contains(search_filter)
                    )
                    query = query.where(search_condition)

                # Order by time
                query = query.order_by(LogEntry.timestamp.asc())

                # Execute query
                new_logs = session.exec(query).all()

                # Send new logs
                for log in new_logs:
                    log_data = _log_entry_to_response(log)
                    yield f"data: {json.dumps(log_data.model_dump())}\n\n"
                    last_check_time = max(last_check_time, log.timestamp)

                # Update check time
                if not new_logs:
                    last_check_time = datetime.now()

        except Exception as e:
            # Send error message
            error_data = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"

        # Wait for a while before checking again
        await asyncio.sleep(1)


@router.get("/realtime")
async def get_realtime_logs(
    level: Optional[str] = Query(None, description="Log level filter"),
    search: Optional[str] = Query(None, description="Search keyword")
):
    """Real-time log stream (Server-Sent Events)"""
    return StreamingResponse(
        log_stream_generator(level, search),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )
