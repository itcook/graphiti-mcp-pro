from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from pydantic import field_validator

# Import ALL dynamically generated Setting models
from .settings_model_generator import Setting, SettingResponse, SettingUpdate


class TokenUsage(SQLModel, table=True):
    """Token usage statistics model"""
    id: Optional[int] = Field(default=None, primary_key=True)
    llm_model_name: str
    episode_name: str | None = None
    response_model: str | None = None
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
    created_at: datetime = Field(default_factory=datetime.now)




class LogEntry(SQLModel, table=True):
    """Log entry model"""
    id: Optional[str] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    level: str = Field(index=True)  # 'info', 'warn', 'error', 'debug'
    message: str = Field(index=True)  # Support search
    source: Optional[str] = Field(default=None, index=True)  # Support search

    @field_validator('level')
    def validate_level(cls, v):
        allowed_levels = ['info', 'warn', 'error', 'debug']
        if v not in allowed_levels:
            raise ValueError(f'level must be one of {allowed_levels}')
        return v


class LogEntryCreate(SQLModel):
    """Log entry creation model for API requests"""
    level: str
    message: str
    source: Optional[str] = None

    @field_validator('level')
    def validate_level(cls, v):
        allowed_levels = ['info', 'warn', 'error', 'debug']
        if v not in allowed_levels:
            raise ValueError(f'level must be one of {allowed_levels}')
        return v


class LogEntryResponse(SQLModel):
    """Log entry response model for API responses"""
    id: str
    timestamp: str  # ISO format string
    level: str
    message: str
    source: Optional[str] = None


class TokenUsageCreate(SQLModel):
    """Token usage statistics creation model for API requests"""
    llm_model_name: str
    episode_name: str
    response_model: str
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
