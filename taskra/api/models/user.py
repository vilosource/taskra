"""Models for Jira users."""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class User(BaseModel):
    """User model for authentication and user information."""
    
    account_id: str = Field(..., alias="accountId") 
    display_name: str = Field(..., alias="displayName")
    email_address: Optional[str] = Field(None, alias="emailAddress")
    active: bool = True
    
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore"
    )
