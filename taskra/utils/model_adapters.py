"""Adapter utilities for backward compatibility with old code."""

from typing import Dict, List, Any, TypeVar, Type, Union, Optional, cast
from datetime import datetime

from ..api.models.worklog import Worklog, Author
from ..api.models.user import User
from ..api.models.issue import Issue, IssueSummary
from ..api.models.project import Project
from ..api.models.comment import Comment
from ..utils.serialization import to_serializable

# Type variable for generic model adapters
ModelT = TypeVar('ModelT')

def adapt_to_dict(model: Any) -> Dict[str, Any]:
    """
    Adapt a Pydantic model to a dictionary format compatible with older code.
    
    This is a convenience wrapper around to_serializable that provides
    consistent formatting and ensures old code expectations are met.
    
    Args:
        model: A Pydantic model instance
        
    Returns:
        Dictionary representation compatible with older code
    """
    return to_serializable(model)

def adapt_from_dict(data: Dict[str, Any], model_class: Type[ModelT]) -> ModelT:
    """
    Adapt a dictionary to a Pydantic model instance.
    
    Args:
        data: Dictionary data, possibly from older code
        model_class: The Pydantic model class to instantiate
        
    Returns:
        An instance of the specified model
    """
    # Check if the model has a from_api class method for handling API responses
    if hasattr(model_class, 'from_api') and callable(getattr(model_class, 'from_api')):
        return cast(ModelT, model_class.from_api(data))
    
    # Otherwise use the standard model constructor
    return model_class.model_validate(data)

def adapt_worklog_for_presentation(worklog: Union[Dict[str, Any], Worklog]) -> Dict[str, Any]:
    """
    Adapt a worklog model or dictionary for the presentation layer.
    
    This ensures consistent field names and structures expected by the UI,
    regardless of whether the input is a model or dictionary.
    
    Args:
        worklog: A Worklog model or dictionary
        
    Returns:
        Dictionary representation ready for the presentation layer
    """
    # Convert to dict if it's a model
    if isinstance(worklog, Worklog):
        worklog_dict = adapt_to_dict(worklog)
    else:
        worklog_dict = worklog
    
    # Ensure expected fields are present for the presentation layer
    result = dict(worklog_dict)
    
    # Add required fields that presentation layer expects
    if "issue_key" in result and "issueKey" not in result:
        result["issueKey"] = result["issue_key"]
    
    if "issue_summary" in result and "issueSummary" not in result:
        result["issueSummary"] = result["issue_summary"]
    
    # Ensure author fields match expected format
    if "author" in result and isinstance(result["author"], dict):
        author = result["author"]
        
        # Ensure displayName is available
        if "display_name" in author and "displayName" not in author:
            author["displayName"] = author["display_name"]
    
    # Ensure time spent fields are properly formatted
    if "time_spent" in result and "timeSpent" not in result:
        result["timeSpent"] = result["time_spent"]
    
    if "time_spent_seconds" in result and "timeSpentSeconds" not in result:
        result["timeSpentSeconds"] = result["time_spent_seconds"]
    
    return result

def adapt_worklogs_list(
    worklogs: List[Union[Dict[str, Any], Worklog]]
) -> List[Dict[str, Any]]:
    """
    Adapt a list of worklogs for the presentation layer.
    
    Args:
        worklogs: List of Worklog models or dictionaries
        
    Returns:
        List of dictionary representations
    """
    return [adapt_worklog_for_presentation(worklog) for worklog in worklogs]

def adapt_user_for_presentation(user: Union[Dict[str, Any], User]) -> Dict[str, Any]:
    """
    Adapt a user model or dictionary for the presentation layer.
    
    Args:
        user: A User model or dictionary
        
    Returns:
        Dictionary representation ready for the presentation layer
    """
    # Convert to dict if it's a model
    if isinstance(user, User):
        user_dict = adapt_to_dict(user)
    else:
        user_dict = user
    
    # Ensure expected fields are present for the presentation layer
    result = dict(user_dict)
    
    # Ensure displayName is available
    if "display_name" in result and "displayName" not in result:
        result["displayName"] = result["display_name"]
    
    # Ensure accountId is available
    if "account_id" in result and "accountId" not in result:
        result["accountId"] = result["account_id"]
    
    # Ensure email field is properly handled
    if "email_address" in result and "emailAddress" not in result:
        result["emailAddress"] = result["email_address"]
    
    return result

def adapt_users_list(users: List[Union[Dict[str, Any], User]]) -> List[Dict[str, Any]]:
    """
    Adapt a list of users for the presentation layer.
    
    Args:
        users: List of User models or dictionaries
        
    Returns:
        List of dictionary representations
    """
    return [adapt_user_for_presentation(user) for user in users]

def adapt_issue_for_presentation(issue: Union[Dict[str, Any], Issue]) -> Dict[str, Any]:
    """
    Adapt an issue model or dictionary for the presentation layer.
    
    Args:
        issue: An Issue model or dictionary
        
    Returns:
        Dictionary representation ready for the presentation layer
    """
    # Convert to dict if it's a model
    if isinstance(issue, Issue):
        issue_dict = adapt_to_dict(issue)
    else:
        issue_dict = issue
    
    # Ensure expected fields are present for the presentation layer
    result = dict(issue_dict)
    
    # Handle fields with potential name mismatches
    if "fields" in result:
        fields = result["fields"]
        
        # Ensure summary is accessible at top level for convenience
        if "summary" in fields and "summary" not in result:
            result["summary"] = fields["summary"]
        
        # Ensure issue type is accessible at top level
        if "issuetype" in fields and "issueType" not in result:
            result["issueType"] = fields["issuetype"]
            
        # Handle status information
        if "status" in fields and isinstance(fields["status"], dict):
            status = fields["status"]
            if "name" in status:
                result["statusName"] = status["name"]
    
    return result

def adapt_issues_list(issues: List[Union[Dict[str, Any], Issue]]) -> List[Dict[str, Any]]:
    """
    Adapt a list of issues for the presentation layer.
    
    Args:
        issues: List of Issue models or dictionaries
        
    Returns:
        List of dictionary representations
    """
    return [adapt_issue_for_presentation(issue) for issue in issues]

def adapt_project_for_presentation(project: Union[Dict[str, Any], Project]) -> Dict[str, Any]:
    """
    Adapt a project model or dictionary for the presentation layer.
    
    Args:
        project: A Project model or dictionary
        
    Returns:
        Dictionary representation ready for the presentation layer
    """
    # Convert to dict if it's a model
    if isinstance(project, Project):
        project_dict = adapt_to_dict(project)
    else:
        project_dict = project
    
    # Ensure expected fields are present for the presentation layer
    result = dict(project_dict)
    
    # Ensure key fields have consistent naming
    if "project_type_key" in result and "projectTypeKey" not in result:
        result["projectTypeKey"] = result["project_type_key"]
    
    # Ensure lead fields are properly formatted
    if "lead" in result and isinstance(result["lead"], dict):
        lead = result["lead"]
        if "display_name" in lead and "displayName" not in lead:
            lead["displayName"] = lead["display_name"]
    
    return result

def adapt_projects_list(projects: List[Union[Dict[str, Any], Project]]) -> List[Dict[str, Any]]:
    """
    Adapt a list of projects for the presentation layer.
    
    Args:
        projects: List of Project models or dictionaries
        
    Returns:
        List of dictionary representations
    """
    return [adapt_project_for_presentation(project) for project in projects]

def adapt_comment_for_presentation(comment: Union[Dict[str, Any], Comment]) -> Dict[str, Any]:
    """
    Adapt a comment model or dictionary for the presentation layer.
    
    Args:
        comment: A Comment model or dictionary
        
    Returns:
        Dictionary representation ready for the presentation layer
    """
    # Convert to dict if it's a model
    if isinstance(comment, Comment):
        comment_dict = adapt_to_dict(comment)
    else:
        comment_dict = comment
    
    # Ensure expected fields are present for the presentation layer
    result = dict(comment_dict)
    
    # Ensure text content is easily accessible
    if isinstance(comment, Comment):
        result["textContent"] = comment.text_content
    elif "body" in result:
        # For dict format, try to extract text from body
        body = result["body"]
        if isinstance(body, dict) and "content" in body:
            # Try to extract text from ADF
            try:
                text_parts = []
                for item in body["content"]:
                    if "content" in item:
                        for child in item["content"]:
                            if child.get("type") == "text":
                                text_parts.append(child.get("text", ""))
                result["textContent"] = " ".join(text_parts)
            except (KeyError, TypeError):
                result["textContent"] = "Complex comment format"
        elif isinstance(body, str):
            result["textContent"] = body
    
    # Ensure author information is properly formatted
    if "author" in result and isinstance(result["author"], dict):
        author = result["author"]
        if "display_name" in author and "displayName" not in author:
            author["displayName"] = author["display_name"]
    
    return result

def adapt_comments_list(comments: List[Union[Dict[str, Any], Comment]]) -> List[Dict[str, Any]]:
    """
    Adapt a list of comments for the presentation layer.
    
    Args:
        comments: List of Comment models or dictionaries
        
    Returns:
        List of dictionary representations
    """
    return [adapt_comment_for_presentation(comment) for comment in comments]
