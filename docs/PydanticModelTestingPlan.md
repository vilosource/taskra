# Pydantic Model Testing Plan

This document outlines the strategy for updating and creating tests to align with the Pydantic model standardization effort.

## Test Update Strategy

### Phase 1: Parallel Test Structure (Weeks 1-2)

1. **Create Model-Specific Test Directory**
   - Create `tests/models/` directory structure
   - Implement separate test files for each model module

2. **Develop Model Test Fixtures**
   - Create fixtures for common test data
   - Design serialization/deserialization test helpers
   - Build validation test utilities

3. **Initial Model Tests**
   - Test base model functionality
   - Verify serialization/deserialization with `model_dump_api()`
   - Confirm validation rules are working

### Phase 2: Existing Test Updates (Weeks 3-4)

1. **Inventory Existing Tests**
   - Document all tests using old model patterns
   - Identify dependencies on model behavior
   - Prioritize tests based on model usage

2. **Create Test Compatibility Layer**
   - Implement adapter functions to bridge old and new model interfaces
   - Add test helpers to convert between formats
   - Create temporary compatibility fixtures

3. **Incremental Test Updates**
   - Update tests one module at a time
   - Align with model implementation schedule
   - Run parallel test suites during transition

### Phase 3: Integration Test Updates (Weeks 5-6)

1. **Update Mock Responses**
   - Update API mock fixtures
   - Create model-based response factories
   - Implement model validation in mocks

2. **Service Layer Test Updates**
   - Update service tests to use model instances
   - Test proper serialization for API calls
   - Verify model transformation logic

3. **End-to-End Flow Testing**
   - Update command tests
   - Test presenter compatibility
   - Verify cache serialization/deserialization

## Testing Standards

### Model Unit Tests

Each model should have tests that verify:

1. **Construction**
   - From raw dictionaries
   - From keyword arguments
   - From other models

2. **Validation**
   - Required fields
   - Field constraints
   - Complex validation rules

3. **Serialization**
   - To/from JSON
   - Model_dump with various options
   - Datetime handling

### Example Model Test

```python
def test_worklog_create_from_simple():
    """Test creating a worklog from simple time format."""
    # Given
    time_str = "2h 30m"
    comment = "Test comment"
    
    # When
    worklog = WorklogCreate.from_simple(time_str, comment)
    
    # Then
    assert worklog.time_spent_seconds == 9000  # 2.5 hours
    assert worklog.comment == comment
    
    # Verify serialization
    data = worklog.model_dump_api()
    assert "timeSpentSeconds" in data
    assert data["timeSpentSeconds"] == 9000
```

### Integration Tests

For integration points:

1. **Cache Integration**
   - Test roundtrip through cache
   - Verify field preservation
   - Test with complex nested models

2. **API Client Integration**
   - Test serialization for requests
   - Test deserialization of responses
   - Verify error handling

3. **Command-to-Presentation Flow**
   - Test end-to-end data flow
   - Verify field mapping
   - Test rendering with model data

## Test Fixtures

Create standardized fixtures for:

1. **Sample Model Data**
   - Basic instances of each model
   - Complex nested model structures
   - Edge case examples

2. **API Response Samples**
   - Standard response patterns
   - Error responses
   - Pagination examples

3. **Serialization Verifiers**
   - Helper functions to verify correct serialization
   - Comparators for model equality
   - Debug tools for model differences

## Migration Timeline

1. **Week 1-2**: Setup test structure and base test helpers
2. **Week 3-4**: Update core model tests
3. **Week 5-6**: Update service and integration tests
4. **Week 7-8**: Update command and UI tests
5. **Week 9**: Final validation and compatibility checking

## Test Compatibility Considerations

- Maintain backward compatibility tests during transition
- Use feature flags to toggle between implementations when needed
- Document model version compatibility in test fixtures
- Label tests with migration status (e.g. `@pytest.mark.uses_new_models`)

## Metrics and Coverage

- Aim for 90%+ test coverage of model code
- Test all validation rules explicitly 
- Verify all serialization edge cases
- Include performance tests for large model collections

## Current Test Implementation Status

### Completed Tests
- ✅ Base model functionality (field conversion, serialization)
- ✅ Model validation rules
- ✅ WorklogService integration tests
- ✅ Core layer serialization
- ✅ Edge case handling tests (complex nested structures, datetime handling)
- ✅ Complex field validation

### In Progress
- 🔄 Backward compatibility adapters testing
- 🔄 UI integration tests
- 🔄 Cache integration tests

### Pending
- 📅 Performance benchmarking
- 📅 User module tests
- 📅 Issue module tests

## Recent Test Implementation

### Edge Case Tests
We've implemented comprehensive edge case tests for the worklog serialization:

1. **Complex Nested Objects**: Testing proper serialization of deeply nested objects like complex comments and author information with avatar URLs.

2. **DateTime Handling**: Testing correct serialization of datetime objects, including those with timezone information.

3. **Empty Fields**: Validating that None values and empty fields are properly preserved during serialization.

4. **API Integration**: Testing worklog creation with complex comment structures.

### Backward Compatibility
We've created adapter functions to ensure backward compatibility:

1. **Model to Dict Conversion**: Functions to convert models to dictionaries expected by older code.

2. **Dict to Model Conversion**: Functions to create model instances from dictionary data.

3. **Presentation Layer Adapters**: Specific functions to ensure data meets presentation layer expectations.

## Model-Specific Test Structure

Each model now has its own test file structure:
- `test_base_models.py` - Basic model functionality
- `test_worklog_service.py` - Service layer integration
- `test_core_worklog_integration.py` - Core layer integration
- `test_worklog_serialization_edge_cases.py` - Edge cases and complex scenarios
