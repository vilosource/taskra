"""Tests for base Pydantic model classes."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from taskra.api.models.base import (
    BaseJiraModel, BaseJiraListModel, ApiResource, TimestampedResource, to_camel
)

class TestBaseModels:
    """Tests for base model functionality."""
    
    def test_to_camel(self):
        """Test snake_case to camelCase conversion."""
        assert to_camel("snake_case") == "snakeCase"
        assert to_camel("multiple_word_snake_case") == "multipleWordSnakeCase"
        assert to_camel("single") == "single"
        assert to_camel("") == ""
    
    def test_base_jira_model_serialization(self):
        """Test BaseJiraModel serialization with aliases."""
        class TestModel(BaseJiraModel):
            snake_case_field: str
            another_field: int
        
        model = TestModel(snakeCaseField="test", anotherField=123)
        
        # Test property access uses snake_case
        assert model.snake_case_field == "test"
        assert model.another_field == 123
        
        # Test serialization uses camelCase
        data = model.model_dump_api()
        assert "snakeCaseField" in data
        assert "anotherField" in data
        assert data["snakeCaseField"] == "test"
        assert data["anotherField"] == 123
    
    def test_base_jira_model_deserialization(self):
        """Test BaseJiraModel deserialization with either case."""
        class TestModel(BaseJiraModel):
            snake_case_field: str
            another_field: int
        
        # Test loading with snake_case
        model1 = TestModel(snake_case_field="test1", another_field=123)
        assert model1.snake_case_field == "test1"
        
        # Test loading with camelCase
        model2 = TestModel(snakeCaseField="test2", anotherField=456)
        assert model2.snake_case_field == "test2"
    
    def test_from_api(self):
        """Test from_api classmethod with validation errors."""
        class TestModel(BaseJiraModel):
            required_field: str
            optional_field: int = 0
        
        # Test with valid data
        valid_data = {"requiredField": "value", "optionalField": 123}
        model = TestModel.from_api(valid_data)
        assert model.required_field == "value"
        assert model.optional_field == 123
        
        # Test with invalid data - should still create model with partial data
        invalid_data = {"optionalField": "not an int"}
        model = TestModel.from_api(invalid_data)
        
        # The model should be created with default values since the data was invalid
        assert model.optional_field == 0  # Default value should be used
        assert model.required_field == ""  # Empty string is the default for str fields


class TestApiResource:
    """Tests for ApiResource model."""
    
    def test_api_resource_validation(self):
        """Test URL validation in ApiResource."""
        # Valid URL
        resource = ApiResource(self="https://example.com/api/resource/123")
        assert resource.self == "https://example.com/api/resource/123"
        
        # Invalid URL
        with pytest.raises(ValidationError):
            ApiResource(self="invalid-url")


class TestTimestampedResource:
    """Tests for TimestampedResource model."""
    
    def test_timestamped_resource(self):
        """Test TimestampedResource fields."""
        now = datetime.now()
        
        resource = TimestampedResource(
            self="https://example.com/api/resource/123",
            created=now,
            updated=now
        )
        
        assert resource.self == "https://example.com/api/resource/123"
        assert resource.created == now
        assert resource.updated == now
        
        # Test serialization
        data = resource.model_dump_api()
        assert "self" in data
        assert "created" in data
        assert "updated" in data
