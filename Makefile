.PHONY: dev run install install-dev sync clean test

# Start development server with hot reload
dev:
	uv run uvicorn app.main:app --reload

# Start production server
run:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Install dependencies
install:
	uv sync

# Install with dev dependencies
install-dev:
	uv sync --extra dev

# Sync dependencies
sync:
	uv lock
	uv sync

# Run tests
test:
	uv run --extra dev pytest tests/ -v

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
