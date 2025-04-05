"""Models for Jira users."""

from typing import Dict, Optional
from pydantic import Field, field_validator

from .base import BaseJiraModel, ApiResource


class UserAvatar(BaseJiraModel):
    """
    User avatar URLs in various sizes.
    
    This class models the avatar URLs for a Jira user, providing standardized access
    to the same avatar image in different resolutions. Jira provides avatar images
    in four standard sizes (16x16, 24x24, 32x32, and 48x48 pixels), which are used
    in different contexts throughout the UI. This model provides semantic naming
    (small, medium, large, xlarge) while maintaining the original size-based aliases.
    
    The model includes validation to ensure all URLs are properly formatted.
    """
    
    small: str = Field(..., alias="16x16", description="16x16 pixel avatar URL")
    medium: str = Field(..., alias="24x24", description="24x24 pixel avatar URL")
    large: str = Field(..., alias="32x32", description="32x32 pixel avatar URL")
    xlarge: str = Field(..., alias="48x48", description="48x48 pixel avatar URL")
    
    @field_validator("small", "medium", "large", "xlarge")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """
        Validate avatar URLs.
        
        Ensures that all avatar URLs are properly formatted with http or https protocol.
        
        Args:
            v: URL string to validate
            
        Returns:
            The validated URL string
            
        Raises:
            ValueError: If URL doesn't start with http:// or https://
        """
        if not v.startswith(("http://", "https://")):
            raise ValueError("Avatar URL must start with http:// or https://")
        return v


class User(ApiResource):
    """
    User model representing a Jira user.
    
    This class represents a user in the Jira system, containing the user's identifying 
    information, display attributes, and account settings. It extends the ApiResource class,
    inheriting standard API resource functionality such as self-URL and validation.
    
    This model is designed to handle user data returned from various Jira API endpoints,
    ensuring consistent representation across the application. It supports optional fields
    to accommodate different levels of detail returned by different endpoints.
    
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
    """
    Extended user model for the currently authenticated user.
    
    This class extends the base User model to include additional information that is
    available only for the currently authenticated user. This includes locale preferences,
    group memberships, and application role assignments, which are not typically available
    when viewing other users.
    
    This model is specifically used with the /rest/api/3/myself endpoint, which returns
    detailed information about the authenticated user making the API request.
    
    API Endpoint: /rest/api/3/myself
    """
    
    locale: Optional[str] = Field(None, description="User's locale")
    groups: Optional[Dict] = Field(None, description="User's groups")
    application_roles: Optional[Dict] = Field(None, description="Application roles")
