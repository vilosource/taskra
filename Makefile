# Makefile for running Taskra tests

.PHONY: tests test-unit test-integration test-config test-api test-core test-cmd test-account clean

# Default Python command
PYTHON := python
# Default pytest command with common options
PYTEST := pytest -v

# Global target to run all tests
tests: test-unit test-integration

# Run all unit tests
test-unit:
	$(PYTEST) tests/unit/

# Run all integration tests
test-integration:
	$(PYTEST) tests/integration/

# Run configuration tests
test-config:
	$(PYTEST) tests/unit/config/

# Run API related tests
test-api:
	$(PYTEST) tests/unit/api/

# Run API services tests
test-api-services:
	$(PYTEST) tests/unit/api/services/

# Run API models tests
test-api-models:
	$(PYTEST) tests/unit/api/models/

# Run core functionality tests
test-core:
	$(PYTEST) tests/unit/core/

# Run command line tests
test-cmd:
	$(PYTEST) tests/unit/cmd/

# Run account management tests
test-account:
	$(PYTEST) tests/unit/config/test_account.py

# Run config manager tests
test-config-manager:
	$(PYTEST) tests/unit/config/test_manager.py

# Run API client tests
test-api-client:
	$(PYTEST) tests/unit/api/test_client.py

# Run with coverage report
test-coverage:
	$(PYTEST) --cov=taskra --cov-report=term --cov-report=html tests/

# Run tests in parallel (useful for large test suites)
test-parallel:
	$(PYTEST) -xvs -n auto tests/

# Generate HTML test report
test-report:
	$(PYTEST) --html=report.html tests/

# Clean up cache and temporary files
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -f report.html
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Help target
help:
	@echo "Available targets:"
	@echo "  tests            : Run all tests"
	@echo "  test-unit        : Run unit tests"
	@echo "  test-integration : Run integration tests"
	@echo "  test-config      : Run configuration tests"
	@echo "  test-api         : Run API tests"
	@echo "  test-api-services: Run API services tests"
	@echo "  test-api-models  : Run API models tests"
	@echo "  test-core        : Run core functionality tests"
	@echo "  test-cmd         : Run command line tests"
	@echo "  test-account     : Run account management tests"
	@echo "  test-config-manager: Run config manager tests"
	@echo "  test-api-client  : Run API client tests"
	@echo "  test-coverage    : Run tests with coverage report"
	@echo "  test-parallel    : Run tests in parallel"
	@echo "  test-report      : Generate HTML test report"
	@echo "  clean            : Clean up temporary files"
