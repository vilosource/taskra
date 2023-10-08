"""Example usage of the new Pydantic models."""

import json
from datetime import datetime
from taskra.api.models.worklog import WorklogCreate, Worklog, Author, WorklogList
from taskra.api.models.user import User

def main():
    """Example usage of worklog models."""
    print("Creating a worklog model...")
    
    # Create a worklog using WorklogCreate.from_simple
    worklog_create = WorklogCreate.from_simple(
        time_spent="2h 30m",
        comment="Working on model standardization",
        started=datetime.now()
    )
    
    print("\nWorklogCreate model created:")
    print(f"Time spent: {worklog_create.time_spent_seconds} seconds")
    print(f"Comment: {worklog_create.comment}")
    print(f"Started: {worklog_create.started}")
    
    # Serialize to API format
    api_data = worklog_create.model_dump_api()
    print("\nSerialized for API (model_dump_api):")
    print(json.dumps(api_data, indent=2, default=str))
    
    # Create an Author model
    author = Author(
        accountId="user123",
        displayName="Test User",
        emailAddress="test@example.com"
    )
    
    # Create a complete Worklog model
    worklog = Worklog(
        id="12345",
        self="https://jira.example.com/rest/api/3/issue/TEST-123/worklog/12345",
        author=author,
        timeSpent="2h 30m",
        timeSpentSeconds=9000,
        started=datetime.now(),
        created=datetime.now(),
        updated=datetime.now(),
        issueId="TEST-123",
        # Add custom fields for internal use
        issueKey="TEST-123",
        issueSummary="Test Issue"
    )
    
    print("\nComplete Worklog model serialized:")
    print(json.dumps(worklog.model_dump_api(), indent=2, default=str))
    
    # Test that the fields can be accessed
    print("\nAccessing fields:")
    print(f"Issue Key: {worklog.issue_key}")
    print(f"Author: {worklog.author.display_name}")
    print(f"Time Spent: {worklog.time_spent}")
    
    # Create a WorklogList
    worklogs_list = WorklogList(
        startAt=0,
        maxResults=50,
        total=1,
        worklogs=[worklog]
    )
    
    print("\nWorklog list serialized:")
    print(json.dumps(worklogs_list.model_dump_api(), indent=2, default=str))


if __name__ == "__main__":
    main()
