"""Models for Jira worklogs."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class Author(BaseModel):
    """Worklog author model."""
    
    account_id: str = Field(..., alias="accountId")
    display_name: str = Field(..., alias="displayName")
    
    model_config = ConfigDict(populate_by_name=True)


class Visibility(BaseModel):
    """Worklog visibility model."""
    
    type: str
    value: str


class Worklog(BaseModel):
    """Detailed worklog model."""
    
    id: str
    self: str
    author: Author
    time_spent: str = Field(..., alias="timeSpent")
    time_spent_seconds: int = Field(..., alias="timeSpentSeconds")
    started: datetime
    created: datetime
    updated: datetime
    comment: Optional[Dict[str, Any]] = None
    issue_id: Optional[str] = Field(None, alias="issueId")
    visibility: Optional[Visibility] = None
    
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class WorklogCreate(BaseModel):
    """Model for creating a new worklog."""
    
    time_spent_seconds: int = Field(..., alias="timeSpentSeconds")
    started: Optional[datetime] = None  # If not provided, current time will be used
    comment: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)
    
    @field_validator("time_spent_seconds")
    def validate_time_spent(cls, v):
        """Validate time spent is positive."""
        if v <= 0:
            raise ValueError("Time spent must be positive")
        return v
    
    @classmethod
    def from_simple(cls, time_spent: str, comment: Optional[str] = None, started: Optional[datetime] = None):
        """
        Create a WorklogCreate instance from a simple time format.
        
        Args:
            time_spent: Time spent in format like "2h 30m" or "3h"
            comment: Optional worklog comment
            started: Optional start time
            
        Returns:
            WorklogCreate instance
        """
        seconds = cls._parse_time_spent(time_spent)
        return cls(
            timeSpentSeconds=seconds,
            comment=comment,
            started=started
        )
    
    @staticmethod
    def _parse_time_spent(time_spent: str) -> int:
        """
        Parse time spent string to seconds.
        
        Args:
            time_spent: Time in format like "2h 30m" or "3h"
            
        Returns:
            Seconds as integer
        """
        total_seconds = 0
        parts = time_spent.split()
        
        for part in parts:
            if part.endswith('h'):
                hours = int(part[:-1])
                total_seconds += hours * 3600
            elif part.endswith('m'):
                minutes = int(part[:-1])
                total_seconds += minutes * 60
            elif part.endswith('s'):
                seconds = int(part[:-1])
                total_seconds += seconds
        
        if total_seconds == 0:
            raise ValueError(f"Invalid time format: {time_spent}. Use format like '2h 30m'.")
        
        return total_seconds


class WorklogList(BaseModel):
    """List of worklogs with pagination info."""
    
    start_at: int = Field(..., alias="startAt")
    max_results: int = Field(..., alias="maxResults")
    total: int
    worklogs: List[Worklog]
    
    model_config = ConfigDict(populate_by_name=True)
