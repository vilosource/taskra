"""Models for Jira worklogs."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pydantic import Field, field_validator, model_validator

from .base import BaseJiraModel, BaseJiraListModel, ApiResource, TimestampedResource
from .user import User  # Import the User model


class Author(BaseJiraModel):
    """
    Represents the author of a worklog entry.
    
    This is a simplified version of User model specific to worklog context.
    """
    account_id: str = Field(..., alias="accountId")
    display_name: str = Field(..., alias="displayName")
    email_address: Optional[str] = Field(None, alias="emailAddress")
    active: Optional[bool] = None
    time_zone: Optional[str] = Field(None, alias="timeZone")
    # Add proper support for avatarUrls field
    avatar_urls: Optional[Dict[str, str]] = Field(None, alias="avatarUrls")
    
    @classmethod
    def from_user(cls, user: User) -> "Author":
        """Create an author from a User model."""
        return cls(
            accountId=user.account_id,
            displayName=user.display_name,
            emailAddress=user.email_address,
            active=user.active,
            timeZone=user.time_zone
        )


class Visibility(BaseJiraModel):
    """
    Worklog visibility model.
    
    Controls who can see this worklog entry.
    """
    type: str = Field(..., description="Type of visibility (group, role, etc.)")
    value: str = Field(..., description="Value for the visibility type")


class Worklog(TimestampedResource):
    """
    Detailed worklog model.
    
    Represents a time tracking entry for an issue.
    
    API Endpoint: GET /rest/api/3/issue/{issueIdOrKey}/worklog/{id}
    """
    id: str = Field(..., description="Worklog ID")
    author: Author = Field(..., description="User who created the worklog")
    time_spent: str = Field(..., description="Human-readable time spent (e.g., '3h 30m')")
    time_spent_seconds: int = Field(..., description="Time spent in seconds")
    started: datetime = Field(..., description="When the work was started")
    comment: Optional[Dict[str, Any]] = Field(None, description="Comment on the worklog")
    issue_id: Optional[str] = Field(None, alias="issueKey", description="ID of the associated issue")
    visibility: Optional[Visibility] = Field(None, description="Worklog visibility settings")
    
    # Additional fields for internal use (not from API)
    issue_key: Optional[str] = Field(None, exclude=True, description="Key of the associated issue")
    issue_summary: Optional[str] = Field(None, exclude=True, description="Summary of the associated issue")

    @property
    def issueKey(self) -> Optional[str]:
        """
        Get the issue key, prioritizing the explicit issue_key field if set.
        This provides backward compatibility for code expecting the issueKey field.
        """
        if self.issue_key:
            return self.issue_key
        return self.issue_id
    
    @issueKey.setter
    def issueKey(self, value: str) -> None:
        """
        Set the issue key.
        This provides backward compatibility for code setting the issueKey field.
        """
        self.issue_key = value
        
    @property
    def issueSummary(self) -> Optional[str]:
        """
        Get the issue summary.
        This provides backward compatibility for code expecting the issueSummary field.
        """
        return self.issue_summary
    
    @issueSummary.setter
    def issueSummary(self, value: str) -> None:
        """
        Set the issue summary.
        This provides backward compatibility for code setting the issueSummary field.
        """
        self.issue_summary = value

    @field_validator("time_spent_seconds")
    @classmethod
    def validate_time_spent(cls, v: int) -> int:
        """Validate that time spent is positive."""
        if v <= 0:
            raise ValueError("Time spent must be positive")
        return v


class WorklogCreate(BaseJiraModel):
    """
    Model for creating a new worklog entry.
    
    API Endpoint: POST /rest/api/3/issue/{issueIdOrKey}/worklog
    """
    time_spent: str = Field(..., alias="timeSpent", description="Time spent in Jira format (e.g., '2h 30m')")
    comment: Optional[Dict[str, Any]] = Field(None, description="Comment on the worklog in ADF format")
    started: str = Field(..., description="When the work was started in ISO format with timezone")
    
    @classmethod
    def from_simple(cls, time_spent: str, comment: Optional[str] = None, started: Optional[datetime] = None) -> "WorklogCreate":
        """
        Create a WorklogCreate instance from a simple time format.
        
        Args:
            time_spent: Time spent in format like "2h 30m" or "3h"
            comment: Optional worklog comment
            started: Optional start time
            
        Returns:
            WorklogCreate instance
        """
        # If no started time is provided, use the current time
        if started is None:
            started = datetime.now()
            
        # Format the datetime in the required Jira API format: yyyy-MM-dd'T'HH:mm:ss.SSSZ
        # Example: 2025-04-05T11:30:00.000+0000
        formatted_date = cls._format_datetime_for_jira(started)
        
        # Format comment as Atlassian Document Format (ADF) if provided
        formatted_comment = None
        if comment:
            formatted_comment = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment
                            }
                        ]
                    }
                ]
            }
        
        # Create the worklog with the properly formatted fields
        return cls(
            timeSpent=time_spent,
            comment=formatted_comment,
            started=formatted_date
        )
    
    @staticmethod
    def _format_datetime_for_jira(dt: datetime) -> str:
        """
        Format a datetime object in the format required by Jira API.
        
        Args:
            dt: Datetime object
            
        Returns:
            Formatted datetime string in the format: yyyy-MM-dd'T'HH:mm:ss.SSSZ
        """
        # Format with milliseconds and timezone offset
        # Example: 2025-04-05T11:30:00.000+0300 for Helsinki time
        
        # Use +0300 for Helsinki timezone as seen in the existing worklog data
        timezone_str = "+0300"
        
        # Format the datetime with milliseconds
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000") + timezone_str
    
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
        
        # Handle formats like "1h30m" without spaces
        if len(parts) == 1 and any(x in parts[0] for x in ['h', 'm', 's']):
            import re
            # Extract hours, minutes, seconds using regex
            hours_match = re.search(r'(\d+)h', parts[0])
            minutes_match = re.search(r'(\d+)m', parts[0])
            seconds_match = re.search(r'(\d+)s', parts[0])
            
            if hours_match:
                total_seconds += int(hours_match.group(1)) * 3600
            if minutes_match:
                total_seconds += int(minutes_match.group(1)) * 60
            if seconds_match:
                total_seconds += int(seconds_match.group(1))
        else:
            # Handle space-separated format like "1h 30m"
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


class WorklogList(BaseJiraListModel):
    """
    List of worklogs with pagination info.
    
    API Endpoint: GET /rest/api/3/issue/{issueIdOrKey}/worklog
    """
    worklogs: List[Worklog] = Field(..., description="List of worklog entries")
