# Variables
ENV = env
PYTHON = $(ENV)/bin/python
PIP = $(ENV)/bin/pip
TEST = pytest
REQS = requirements-dev.txt

# Directories to clean
CLEAN_DIRS = __pycache__ .mypy_cache .pytest_cache

.PHONY: setup install clean test pre-commit lint format help

# Setup the virtual environment
setup:
	@if [ -d "$(ENV)" ]; then \
		echo "Virtual environment already exists. Skipping creation."; \
	else \
		echo "Setting up virtual environment..."; \
		python3 -m venv $(ENV); \
		$(PIP) install --upgrade pip; \
		$(PIP) install -r $(REQS); \
		echo "🛠️ Setup complete 🛠️"; \
	fi

# Install dependencies
install:
	$(PIP) install -r $(REQS)
	@echo "📦 Dependencies installed 📦"

# Clean all specified directories
clean:
	@for dir in $(CLEAN_DIRS); do \
    	find . -name "$$dir" -exec rm -rf {} \; 2>/dev/null || true; \
	done
	@echo "🧹 Cleaned all specified directories 🧹"

# Run tests
test:
	$(TEST) tests
	@echo "🧪 Tests passed 🧪"

coverage:
	$(ENV)/bin/coverage run --source=elevatr -m pytest tests
	$(ENV)/bin/coverage report
	$(ENV)/bin/coverage html
	@echo "📊 Coverage report generated 📊"

# Pre commit
pre-commit:
	pre-commit run --all-files --config .pre-commit-config.yaml
	@echo "🔍 Pre-commit hooks passed 🔍"

# lint code
lint:
	$(ENV)/bin/flake8 --ignore=E501,D202,E402,W503,D100,D104 elevatr tests
	@echo "🛠️ Linting passed 🛠️"

# format code
format:
	$(ENV)/bin/black --line-length 110 elevatr tests
	find . -type f -name "*.py" -not -path "./$(ENV)/*" \
		-exec $(ENV)/bin/docformatter --wrap-summaries 110 --wrap-descriptions 110 --in-place {} +
	@echo "🔄 Code formatted 🔄"

# Display help
help:
	@echo "==================================================================="
	@echo "                         Available targets                         "
	@echo "==================================================================="
	@echo "  setup      - 🛠️ Setup virtual environment and install dependencies"
	@echo "  install    - 📦 Install dependencies"
	@echo "  clean      - 🧹 Clean all specified directories"
	@echo "  test       - 🧪 Run tests"
	@echo "  coverage   - 📊 Generate coverage report"
	@echo "  pre-commit - 🔍 Run pre-commit hooks"
	@echo "  lint       - 🛠️ Lint code"
	@echo "  format     - 🔄 Format code"
	@echo "  help       - ❓ Display this help message"
	@echo "==================================================================="
