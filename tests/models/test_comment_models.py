"""Tests for Comment models and serialization."""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from taskra.api.models.comment import Comment, CommentVisibility, CommentCreate
from taskra.api.models.user import User
from taskra.utils.model_adapters import adapt_comment_for_presentation

class TestCommentModels:
    """Test Comment models."""
    
    def test_comment_serialization(self):
        """Test serializing Comment models."""
        # Create author
        author = User(
            self_url="https://example.com/rest/api/3/user?accountId=123",
            accountId="123",
            displayName="Test User"
        )
        
        # Create a simple text comment
        comment = Comment(
            self_url="https://example.com/rest/api/3/issue/TEST-1/comment/10000",
            id="10000",
            author=author,
            body="This is a comment",
            created=datetime.now(),
            updated=datetime.now()
        )
        
        # Serialize to dictionary
        result = comment.model_dump_api()
        
        # Verify serialization
        assert isinstance(result, dict)
        assert "id" in result
        assert result["id"] == "10000"
        assert "body" in result
        assert result["body"] == "This is a comment"
        assert "author" in result
        assert "displayName" in result["author"]
    
    def test_comment_with_adf_body(self):
        """Test Comment with Atlassian Document Format body."""
        # Create author
        author = User(
            self_url="https://example.com/rest/api/3/user?accountId=123",
            accountId="123",
            displayName="Test User"
        )
        
        # Create a comment with ADF body
        adf_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "This is a comment with formatting"
                        }
                    ]
                }
            ]
        }
        
        comment = Comment(
            self_url="https://example.com/rest/api/3/issue/TEST-1/comment/10000",
            id="10000",
            author=author,
            body=adf_body,
            created=datetime.now(),
            updated=datetime.now()
        )
        
        # Test text content extraction
        text_content = comment.text_content
        assert text_content == "This is a comment with formatting"
    
    def test_comment_create_payload(self):
        """Test CommentCreate model and its API payload generation."""
        # Create a simple comment
        comment_create = CommentCreate(
            body="This is a new comment"
        )
        
        # Generate API payload
        payload = comment_create.to_api_payload()
        
        # Verify payload structure
        assert "body" in payload
        assert payload["body"]["type"] == "doc"
        assert payload["body"]["version"] == 1
        assert isinstance(payload["body"]["content"], list)
        assert len(payload["body"]["content"]) > 0
        assert payload["body"]["content"][0]["content"][0]["text"] == "This is a new comment"
    
    def test_comment_adapter(self):
        """Test comment adapter functions."""
        # Create a comment with ADF body
        adf_body = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "This is a comment with formatting"
                        }
                    ]
                }
            ]
        }
        
        # Create author
        author = User(
            self_url="https://example.com/rest/api/3/user?accountId=123",
            accountId="123",
            displayName="Test User"
        )
        
        comment = Comment(
            self_url="https://example.com/rest/api/3/issue/TEST-1/comment/10000",
            id="10000",
            author=author,
            body=adf_body,
            created=datetime.now(),
            updated=datetime.now()
        )
        
        # Adapt for presentation
        result = adapt_comment_for_presentation(comment)
        
        # Verify textContent was extracted
        assert "textContent" in result
        assert result["textContent"] == "This is a comment with formatting"
        
        # Verify author information is preserved
        assert "author" in result
        assert "displayName" in result["author"]
        assert result["author"]["displayName"] == "Test User"
