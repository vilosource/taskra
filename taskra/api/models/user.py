"""Models for Jira users."""

from typing import Dict, Optional
from pydantic import Field, field_validator

from .base import BaseJiraModel, ApiResource


class UserAvatar(BaseJiraModel):
    """User avatar URLs in various sizes."""
    
    small: str = Field(..., alias="16x16", description="16x16 pixel avatar URL")
    medium: str = Field(..., alias="24x24", description="24x24 pixel avatar URL")
    large: str = Field(..., alias="32x32", description="32x32 pixel avatar URL")
    xlarge: str = Field(..., alias="48x48", description="48x48 pixel avatar URL")
    
    @field_validator("small", "medium", "large", "xlarge")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate avatar URLs."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Avatar URL must start with http:// or https://")
        return v


class User(ApiResource):
    """
    User model representing a Jira user.
    
    API Endpoint: /rest/api/3/user
    """
    
    self_url: str = Field(..., alias="self", description="URL to the user resource")
    account_id: str = Field(..., description="User account ID")
    display_name: str = Field(..., description="User's display name")
    email_address: Optional[str] = Field(None, description="User's email address")
    active: bool = Field(True, description="Whether the user is active")
    avatar_urls: Optional[UserAvatar] = Field(None, description="Avatar URLs")
    time_zone: Optional[str] = Field(None, description="User's time zone")
    account_type: Optional[str] = Field(None, description="Type of account")


class CurrentUser(User):
    """Extended user model for the currently authenticated user."""
    
    locale: Optional[str] = Field(None, description="User's locale")
    groups: Optional[Dict] = Field(None, description="User's groups")
    application_roles: Optional[Dict] = Field(None, description="Application roles")
