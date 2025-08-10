from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, and_
from pydantic import BaseModel
from ..models import TokenUsage, TokenUsageCreate
from ..database import get_session

router = APIRouter(prefix="/token-usage", tags=["token-usage"])

class TokenUsageResponse(BaseModel):
    """Token usage statistics response model"""
    id: int
    llm_model_name: str
    episode_name: str
    response_model: str
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
    created_at: datetime


class PaginatedTokenUsage(BaseModel):
    """Paginated token usage statistics response model"""
    items: List[TokenUsageResponse]
    total: int
    page: int
    page_size: int


class StatItem(BaseModel):
    """Statistics item model"""
    period: str
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int


def create_period_info(**kwargs) -> dict:
    """Create period information dictionary, automatically excluding None values"""
    return {k: v for k, v in kwargs.items() if v is not None}


class PeriodInfo(BaseModel):
    """Period information model"""
    year: Optional[int] = None
    month: Optional[int] = None
    week: Optional[int] = None
    day: Optional[int] = None


class StatDetail(BaseModel):
    """Detailed statistics model"""
    period: dict  # Use dict type to support dynamic fields
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
    details: List[StatItem]


@router.post("/", response_model=TokenUsageResponse)
async def create_token_usage(
    token_usage: TokenUsageCreate,
    session: Session = Depends(get_session)
):
    """Create token usage statistics"""
    db_token_usage = TokenUsage.model_validate(token_usage.model_dump())
    session.add(db_token_usage)
    session.commit()
    session.refresh(db_token_usage)
    return db_token_usage


@router.get("/", response_model=PaginatedTokenUsage)
async def get_token_usage(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    session: Session = Depends(get_session)
):
    """Get token usage statistics with pagination"""
    query = select(TokenUsage)
    
    # Add date filtering
    if start_date:
        query = query.where(TokenUsage.created_at >= start_date)
    if end_date:
        # Use < (end_date + 1 day) to include the entire end date and avoid precision issues
        end_date_next_day = end_date + timedelta(days=1)
        query = query.where(TokenUsage.created_at < end_date_next_day)
    
    # Calculate total count
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()
    
    # Pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(TokenUsage.created_at.desc())
    
    items = session.exec(query).all()

    # Convert to response model
    response_items = [
        TokenUsageResponse(
            id=item.id,
            llm_model_name=item.llm_model_name,
            episode_name=item.episode_name,
            response_model=item.response_model,
            completion_tokens=item.completion_tokens,
            prompt_tokens=item.prompt_tokens,
            total_tokens=item.total_tokens,
            created_at=item.created_at
        )
        for item in items
    ]

    return PaginatedTokenUsage(
        items=response_items,
        total=total,
        page=page,
        page_size=page_size
    )


def _get_total_stats(session: Session, conditions: list) -> tuple:
    """Get total statistics"""
    total_query = select(
        func.sum(TokenUsage.completion_tokens).label("completion_tokens"),
        func.sum(TokenUsage.prompt_tokens).label("prompt_tokens"),
        func.sum(TokenUsage.total_tokens).label("total_tokens")
    ).where(and_(*conditions))

    result = session.exec(total_query).first()
    return (result[0] or 0, result[1] or 0, result[2] or 0)


def _get_hourly_stats(session: Session, target_date: datetime) -> List[StatItem]:
    """Get hourly statistics for specified date"""
    start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    conditions = [
        TokenUsage.created_at >= start_of_day,
        TokenUsage.created_at < end_of_day
    ]

    hour_query = select(
        func.strftime("%H", TokenUsage.created_at).label("hour"),
        func.sum(TokenUsage.completion_tokens).label("completion_tokens"),
        func.sum(TokenUsage.prompt_tokens).label("prompt_tokens"),
        func.sum(TokenUsage.total_tokens).label("total_tokens")
    ).where(and_(*conditions)).group_by("hour").order_by("hour")

    hour_results = session.exec(hour_query).all()

    # Create complete 24-hour data (including hours with no data)
    hourly_data = {}
    for row in hour_results:
        hourly_data[int(row[0])] = StatItem(
            period=f"{row[0]}:00",
            completion_tokens=row[1] or 0,
            prompt_tokens=row[2] or 0,
            total_tokens=row[3] or 0
        )

    # Fill missing hours
    details = []
    for hour in range(24):
        if hour in hourly_data:
            details.append(hourly_data[hour])
        else:
            details.append(StatItem(
                period=f"{hour:02d}:00",
                completion_tokens=0,
                prompt_tokens=0,
                total_tokens=0
            ))

    return details


def _get_daily_stats_for_period(session: Session, start_date: datetime, end_date: datetime) -> List[StatItem]:
    """Get daily statistics for specified time period"""
    conditions = [
        TokenUsage.created_at >= start_date,
        TokenUsage.created_at < end_date
    ]

    day_query = select(
        func.strftime("%Y-%m-%d", TokenUsage.created_at).label("date"),
        func.sum(TokenUsage.completion_tokens).label("completion_tokens"),
        func.sum(TokenUsage.prompt_tokens).label("prompt_tokens"),
        func.sum(TokenUsage.total_tokens).label("total_tokens")
    ).where(and_(*conditions)).group_by("date").order_by("date")

    day_results = session.exec(day_query).all()

    return [
        StatItem(
            period=row[0],
            completion_tokens=row[1] or 0,
            prompt_tokens=row[2] or 0,
            total_tokens=row[3] or 0
        )
        for row in day_results
    ]


def _get_current_week_info(now: datetime) -> tuple[int, int]:
    """Get year and ISO week number for current date"""
    year, week, _ = now.isocalendar()
    return year, week


def _get_week_start_end(year: int, week: int) -> tuple[datetime, datetime]:
    """Calculate week start and end dates based on year and ISO week number"""
    # ISO week starts on Monday
    jan_4 = datetime(year, 1, 4)
    week_start = jan_4 - timedelta(days=jan_4.weekday()) + timedelta(weeks=week-1)
    week_end = week_start + timedelta(days=7)
    return week_start, week_end


@router.get("/stats/daily", response_model=StatDetail)
async def get_daily_stats(
    day: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """Get token usage statistics by day, return hourly details

    - day=YYYY-MM-DD: Return statistics for specified date
    - No day parameter: Return today's statistics
    """
    now = datetime.now()

    if day:
        try:
            target_date = datetime.strptime(day, "%Y-%m-%d")
        except ValueError:
            # Invalid parameter, use today
            target_date = now
    else:
        # Default to today
        target_date = now

    start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    conditions = [
        TokenUsage.created_at >= start_of_day,
        TokenUsage.created_at < end_of_day
    ]

    completion_tokens, prompt_tokens, total_tokens = _get_total_stats(session, conditions)
    details = _get_hourly_stats(session, target_date)

    return StatDetail(
        period=create_period_info(
            year=target_date.year,
            month=target_date.month,
            day=target_date.day
        ),
        completion_tokens=completion_tokens,
        prompt_tokens=prompt_tokens,
        total_tokens=total_tokens,
        details=details
    )


@router.get("/stats/weekly", response_model=StatDetail)
async def get_weekly_stats(
    week: Optional[int] = None,
    year: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Get token usage statistics by week, return daily details

    - week=1-53, year=YYYY: Return statistics for specified year and week
    - week=1-53: Return statistics for specified week of current year
    - No parameters: Return current week statistics
    """
    now = datetime.now()

    if week is None:
        # Get current week
        current_year, current_week = _get_current_week_info(now)
        target_year = year if year else current_year
        target_week = current_week
    else:
        # Validate week number
        if not (1 <= week <= 53):
            # Invalid parameter, use current week
            current_year, current_week = _get_current_week_info(now)
            target_year = year if year else current_year
            target_week = current_week
        else:
            target_year = year if year else now.year
            target_week = week

    # Validate year
    if target_year < 1900 or target_year > 2100:
        current_year, current_week = _get_current_week_info(now)
        target_year = current_year
        target_week = current_week

    week_start, week_end = _get_week_start_end(target_year, target_week)

    conditions = [
        TokenUsage.created_at >= week_start,
        TokenUsage.created_at < week_end
    ]

    completion_tokens, prompt_tokens, total_tokens = _get_total_stats(session, conditions)
    details = _get_daily_stats_for_period(session, week_start, week_end)

    return StatDetail(
        period=create_period_info(
            year=target_year,
            week=target_week
        ),
        completion_tokens=completion_tokens,
        prompt_tokens=prompt_tokens,
        total_tokens=total_tokens,
        details=details
    )


@router.get("/stats/monthly", response_model=StatDetail)
async def get_monthly_stats(
    month: Optional[int] = None,
    year: Optional[int] = None,
    session: Session = Depends(get_session)
):
    """Get token usage statistics by month, return daily details

    - month=1-12, year=YYYY: Return statistics for specified year and month
    - month=1-12: Return statistics for specified month of current year
    - No parameters: Return current month statistics
    """
    now = datetime.now()

    if month is None:
        # Use current month
        target_year = year if year else now.year
        target_month = now.month
    else:
        # Validate month
        if not (1 <= month <= 12):
            # Invalid parameter, use current month
            target_year = year if year else now.year
            target_month = now.month
        else:
            target_year = year if year else now.year
            target_month = month

    # Validate year
    if target_year < 1900 or target_year > 2100:
        target_year = now.year
        target_month = now.month

    month_start = datetime(target_year, target_month, 1)
    if target_month == 12:
        month_end = datetime(target_year + 1, 1, 1)
    else:
        month_end = datetime(target_year, target_month + 1, 1)

    conditions = [
        TokenUsage.created_at >= month_start,
        TokenUsage.created_at < month_end
    ]

    completion_tokens, prompt_tokens, total_tokens = _get_total_stats(session, conditions)
    details = _get_daily_stats_for_period(session, month_start, month_end)

    return StatDetail(
        period=create_period_info(
            year=target_year,
            month=target_month
        ),
        completion_tokens=completion_tokens,
        prompt_tokens=prompt_tokens,
        total_tokens=total_tokens,
        details=details
    )
