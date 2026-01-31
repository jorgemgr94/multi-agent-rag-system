# Multi-Agent RAG System - Agent Guidelines

This file contains development guidelines for agentic coding agents working in this repository.

## Build/Lint/Test Commands

### Development Environment
- **Package Manager**: `uv` (required)
- **Python Version**: 3.11+

### Core Commands
```bash
# Install dependencies
make install              # Production dependencies
make install-dev          # Include dev dependencies (pytest, httpx)

# Development servers
make dev                  # FastAPI with hot reload (port 8000)
make run                  # Production FastAPI server
make dashboard            # Streamlit dashboard (port 8501)

# Testing
make test                 # Run all tests
uv run --extra dev pytest tests/ -v  # Direct pytest call

# Single test execution
uv run --extra dev pytest tests/test_briefing_agents.py -v
uv run --extra dev pytest tests/test_retriever_agent.py::TestRetrieverAgent::test_retrieve -v

# Code quality (run these after changes)
ruff check .              # Linting
ruff format .             # Formatting
```

## Code Style Guidelines

### Import Organization
- Use `ruff` for formatting (line length: 88)
- Standard imports: `os`, `sys`, `pathlib`
- Third-party: `fastapi`, `pydantic`, `langchain`, `pytest`
- Local imports: `from app.core import ...`, `from app.briefings import ...`
- Known first-party packages: `app`, `dashboard`

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `RetrieverAgent`, `SpecialistResult`)
- **Functions/Methods**: `snake_case` (e.g., `generate_briefing`, `_build_queries`)
- **Variables**: `snake_case` (e.g., `company_name`, `retrieval_filters`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_MODEL`)
- **Private methods**: Prefix with `_` (e.g., `_synthesize`, `_collect_sources`)

### Type Hints
- **Required**: All functions must have type hints
- **Use**: `str | None` for optional types (Python 3.11+ syntax)
- **Collections**: `list[str]`, `dict[str, Any]`, `set[str]`
- **Custom types**: Use Pydantic models for structured data
- **Abstract methods**: Must be fully typed in parent class

### Error Handling
- **Specific exceptions**: Catch specific exceptions, not bare `except:`
- **Logging**: Use structured logging via `app.core.get_logger(__name__)`
- **Graceful degradation**: Agents should return partial results on failure
- **Error propagation**: Let critical errors bubble up, handle non-critical ones locally

### Agent Architecture Patterns

#### Base Agent Implementation
```python
class SpecialistAgent(BaseAgent):
    name: str = "agent_name"
    description: str = "Brief description"
    
    def __init__(self, retriever: RetrieverAgent):
        self.retriever = retriever
        self.llm = ChatOpenAI(api_key=settings.openai_api_key)
    
    def execute(self, context: dict[str, Any]) -> SpecialistResult:
        # 1. Build queries
        # 2. Retrieve documents  
        # 3. Synthesize findings
        # 4. Return structured result
```

#### Specialist Agent Workflow
1. **Query Building**: Convert context to search queries
2. **Retrieval**: Use RetrieverAgent with filters
3. **Synthesis**: Format context and call LLM
4. **Result**: Return `SpecialistResult` with sources

### Configuration Management
- **Environment**: Use `pydantic-settings` `BaseSettings`
- **API Keys**: Store in `.env` as `SecretStr`
- **Defaults**: Provide sensible defaults in settings
- **Feature flags**: Use config for optional features

### Testing Patterns
- **Fixtures**: Create reusable fixtures with `@pytest.fixture`
- **Mocking**: Use `unittest.mock` for external dependencies
- **Test structure**: Arrange-Act-Assert pattern
- **Coverage**: Test success, failure, and edge cases

### Database/Vector Store
- **Factory pattern**: Use `VectorStoreFactory` for store creation
- **Abstractions**: Code against `BaseVectorStore` interface
- **Configuration**: Store type via env var (`vector_store_type`)
- **Filters**: Apply at retrieval time, not storage

### File Organization
```
app/
├── core/           # Shared utilities, config, base classes
├── briefings/      # Briefing generation agents
├── documents/      # Document processing and retrieval
└── main.py         # FastAPI application entry
tests/              # Test files mirror app structure
dashboard/          # Streamlit UI (separate concern)
```

### LLM Integration
- **Model**: Default to `gpt-4o-mini`, configurable via settings
- **Temperature**: 0.0 for retrieval, 0.3 for synthesis
- **Prompts**: Use f-strings for context injection
- **Response parsing**: Handle JSON parsing errors gracefully

### API Design
- **Pydantic schemas**: All request/response models
- **Router organization**: One router per feature domain
- **Error responses**: Consistent error format
- **Validation**: Let Pydantic handle input validation

### Performance Considerations
- **Retrieval limits**: Use `top_k` to limit context
- **Async patterns**: Use FastAPI async patterns where beneficial
- **Caching**: Cache vector store connections
- **Monitoring**: Log timing and token usage

### Security
- **No secrets in code**: Always use environment variables
- **Input validation**: Validate all external inputs
- **Rate limiting**: Consider for production deployments
- **Logging**: Don't log sensitive data

## Git Conventions
- **Format**: `type(scope): description`
- **Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- **Subject**: Under 50 characters, imperative mood
- **Examples**: `feat(briefings): add competitor analysis agent`

## Key Files to Understand
- `app/core/config.py`: Settings and configuration
- `app/core/agents/base.py`: Base agent interface
- `app/briefings/agents/base.py`: Specialist agent pattern
- `app/documents/agents/retriever.py`: RAG implementation
- `pyproject.toml`: Dependencies and tool configuration
- `Makefile`: Development commands

## Before Committing
1. Run `make test` - ensure all tests pass
2. Run `ruff check .` - fix any linting issues
3. Run `ruff format .` - format code consistently
4. Verify imports are organized correctly
5. Check type hints are complete and accurate