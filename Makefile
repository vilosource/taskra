# Taskra Makefile - Development and testing utilities

.PHONY: clean test test-all test-core test-models test-integration lint examples setup

# Default Python interpreter
PYTHON = python
# Default pytest command with common options
PYTEST = pytest -v
# Default coverage command
COVERAGE = coverage

# Project directories
SRC_DIR = taskra
TEST_DIR = tests
DOC_DIR = docs
CACHE_DIR = ~/.taskra/cache

# Test targets
test: test-all

# Run all tests
test-all:
	$(PYTEST) $(TEST_DIR)

# Run only core tests
test-core:
	$(PYTEST) $(TEST_DIR)/core

# Run only model tests (new)
test-models:
	$(PYTEST) $(TEST_DIR)/models

# Run only integration tests
test-integration:
	$(PYTEST) $(TEST_DIR)/integration

# Run example scripts
examples:
	$(PYTHON) -m tests.examples.worklog_model_example

# Run tests with coverage
coverage:
	$(COVERAGE) run -m pytest $(TEST_DIR)
	$(COVERAGE) report -m
	$(COVERAGE) html

# Lint the code
lint:
	flake8 $(SRC_DIR) $(TEST_DIR)
	mypy $(SRC_DIR)

# Setup development environment
setup:
	pip install -e .
	pip install -r requirements-dev.txt

# Clean cache and temporary files
clean:
	rm -rf .pytest_cache
	rm -rf .coverage htmlcov
	rm -rf __pycache__ $(SRC_DIR)/__pycache__ $(TEST_DIR)/__pycache__
	rm -rf $(CACHE_DIR)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Watch and run tests on file changes (requires watchdog)
watch:
	watchmedo shell-command \
		--patterns="*.py" \
		--recursive \
		--command='make test-models' \
		$(SRC_DIR) $(TEST_DIR)/models

# Documentation
doc:
	cd $(DOC_DIR) && mkdocs build

# Serve documentation
doc-serve:
	cd $(DOC_DIR) && mkdocs serve

# Help command
help:
	@echo "Available targets:"
	@echo "  test        - Run all tests"
	@echo "  test-all    - Run all tests (same as test)"
	@echo "  test-core   - Run only core tests"
	@echo "  test-models - Run only model tests"
	@echo "  test-integration - Run only integration tests" 
	@echo "  examples    - Run example scripts"
	@echo "  coverage    - Run tests with coverage report"
	@echo "  lint        - Check code style and quality"
	@echo "  setup       - Set up development environment"
	@echo "  clean       - Remove temporary files"
	@echo "  watch       - Watch for file changes and run tests"
	@echo "  doc         - Build documentation"
	@echo "  doc-serve   - Serve documentation locally"
