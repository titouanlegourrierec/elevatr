PYTHON = python3
VENV = env
PROJECT_NAME = elevatr

# Directories and files to clean up
CLEAN_DIRS = __pycache__ .pytest_cache .mypy_cache htmlcov
CLEAN_FILES = *.pyc *.pyo *.pyd .coverage

# Ignore flake8 errors
FLAKE8_IGNORE = E501,W503

# Create virtual environment and install dependencies
.PHONY: setup
setup:
	@$(PYTHON) -m venv $(VENV) && \
	. $(VENV)/bin/activate && \
	$(VENV)/bin/pip install -r requirements-dev.txt
	@echo "🛠️ Setup complete 🛠️"

# Install dependencies
.PHONY: install-deps
install-deps:
	@. $(VENV)/bin/activate && \
	$(VENV)/bin/pip install -r requirements-dev.txt > /dev/null 2>&1 && \
	$(VENV)/bin/pip install -r docs/requirements-docs.txt > /dev/null 2>&1

# Clean up files and directories
.PHONY: clean
clean:
	@for dir in $(CLEAN_DIRS); do \
		find . -name "$$dir" -exec rm -rf {} \; 2>/dev/null || true; \
	done
	@for file in $(CLEAN_FILES); do \
		find . -name "$$file" -exec rm -f {} \; 2>/dev/null || true; \
	done
	@echo "🧹 Cleaned up 🧹"

# Lint the code
.PHONY: lint
lint: install-deps
	@. $(VENV)/bin/activate && \
	FILES="$(PROJECT_NAME) $(if $(wildcard tests/),tests/)" && \
	$(VENV)/bin/black -l 110 $$FILES && \
	$(VENV)/bin/flake8 --ignore=$(FLAKE8_IGNORE) $$FILES && \
	$(VENV)/bin/isort $$FILES && \
	$(VENV)/bin/mypy --ignore-missing-imports $$FILES
	@echo "🔄 code linted 🔄"

# Run tests
.PHONY: test
test: install-deps
	@. $(VENV)/bin/activate && \
	$(VENV)/bin/pytest -n auto tests/
	@echo "🧪 Tests passed 🧪"

# Run tests with coverage
.PHONY: coverage
coverage: install-deps
	@. $(VENV)/bin/activate && \
	$(VENV)/bin/coverage run --source=$(PROJECT_NAME) -m pytest tests/ && \
	$(VENV)/bin/coverage report
	$(VENV)/bin/coverage html
	@echo "🧪 Tests passed 🧪"

# Build the documentation
.PHONY: docs
docs: install-deps
	@. $(VENV)/bin/activate && \
	cd docs && make html
	open docs/build/html/index.html
	@echo "📚 Documentation built 📚"

# Display help
.PHONY: help
help:
	@echo "====================================================================="
	@echo "====                      Available targets                      ===="
	@echo "====================================================================="
	@echo "  setup      - 🛠️ Setup virtual environment and install dependencies"
	@echo "  clean      - 🧹 Clean up files and directories"
	@echo "  lint       - 🔄 Lint the code"
	@echo "  test       - 🧪 Run tests"
	@echo "  coverage   - 🧪 Run tests with coverage"
	@echo "  docs       - 📚 Build the documentation"
	@echo "  help       - ❓ Display this help message"
	@echo "====================================================================="
