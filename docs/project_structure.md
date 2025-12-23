# Project Structure

This document describes the organization and architecture of the Echo project.

## Directory Structure

```
echo/
├── .github/                    # GitHub-specific files
│   └── copilot-instructions.md # GitHub Copilot project context
├── docs/                       # Documentation
│   ├── basic_concepts.md
│   ├── Design.md
│   ├── modes.md
│   ├── shared_responsibility_model.md
│   └── bruno_collection/       # API testing collection
├── examples/                   # Example data and configurations
│   ├── data/                   # Sample data files
│   │   ├── Employees.json
│   │   ├── Reviewables1.json
│   │   └── Reviewables2.json
│   └── README.md
├── scripts/                    # Utility scripts
│   └── README.md
├── src/                        # Application source code
│   ├── api/                    # API layer - HTTP handling
│   │   ├── routes/
│   │   │   ├── basic.py        # HTML/template routes
│   │   │   └── campaigns.py    # REST API routes
│   │   └── __init__.py
│   ├── core/                   # Core layer - Domain logic
│   │   ├── config.py           # Configuration management
│   │   ├── employees.py        # Employee data access
│   │   ├── lifecycle.py        # Application lifecycle
│   │   ├── models.py           # Pydantic domain models
│   │   ├── scheduler.py        # AWS EventBridge integration
│   │   └── __init__.py
│   ├── db/                     # Database layer - Persistence
│   │   ├── db_engine.py        # Database engine configuration
│   │   ├── schemas.py          # SQLAlchemy models
│   │   └── __init__.py
│   ├── services/               # Service layer - Business operations
│   │   ├── campaign_service.py # Campaign CRUD + scheduler coordination
│   │   └── __init__.py
│   ├── templates/              # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── create.html
│   │   ├── delete.html
│   │   ├── index.html
│   │   ├── list.html
│   │   ├── show.html
│   │   └── update.html
│   ├── utils/                  # Utility modules
│   │   ├── queue_watcher.py
│   │   └── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   └── __init__.py
├── tests/                      # Test suite
│   ├── conftest.py             # Pytest fixtures and configuration
│   └── __init__.py
├── .gitignore
├── .pylintrc
├── .python-version
├── pyproject.toml              # Project metadata and dependencies
├── pyrightconfig.json
├── README.md
└── uv.lock
```

## Architecture Layers

### 1. API Layer (`src/api/`)
- **Purpose:** HTTP request/response handling, validation, routing
- **Components:**
  - `routes/basic.py` - HTML template routes (no `/api` prefix)
  - `routes/campaigns.py` - RESTful API routes (`/api/campaigns`)
- **Responsibilities:**
  - Request validation (via Pydantic)
  - Response formatting
  - HTTP status codes
  - Route registration

### 2. Service Layer (`src/services/`)
- **Purpose:** Business logic orchestration
- **Components:**
  - `campaign_service.py` - Campaign CRUD operations + AWS scheduler coordination
- **Responsibilities:**
  - Transaction management
  - Business rule enforcement
  - Coordination between domain, database, and external services
  - Domain/schema model conversion

### 3. Core Layer (`src/core/`)
- **Purpose:** Domain models and core utilities
- **Components:**
  - `models.py` - Pydantic domain models (Campaign, Employee, etc.)
  - `config.py` - Application configuration
  - `scheduler.py` - AWS EventBridge scheduler client
  - `lifecycle.py` - Application startup/shutdown
  - `employees.py` - Employee data access (example)
- **Responsibilities:**
  - Domain model definitions
  - Business constants
  - External service clients
  - Configuration management

### 4. Database Layer (`src/db/`)
- **Purpose:** Data persistence
- **Components:**
  - `schemas.py` - SQLAlchemy ORM models
  - `db_engine.py` - Database engine and connection management
- **Responsibilities:**
  - Database schema definitions
  - Database connection management
  - Table creation/migration

## Key Design Patterns

### Layered Architecture
```
┌─────────────────────────────────────┐
│  API Layer (api/routes/)            │  ← FastAPI routes & HTTP
├─────────────────────────────────────┤
│  Service Layer (services/)          │  ← Business logic orchestration
├─────────────────────────────────────┤
│  Core Layer (core/)                 │  ← Domain models & utilities
├─────────────────────────────────────┤
│  Database Layer (db/)               │  ← Persistence
└─────────────────────────────────────┘
```

### Dependency Flow
- API depends on Services and Core
- Services depend on Core and Database
- Core is independent (no dependencies on other layers)
- Database is independent (only depends on Core for minimal types)

### Domain Model Separation
- **Pydantic Models** (`core/models.py`) - Domain layer, API contracts
- **SQLAlchemy Models** (`db/schemas.py`) - Persistence layer
- **Conversion Functions** - Service layer handles to_domain()/to_schema()

## File Naming Conventions

- **Modules:** `snake_case.py` (e.g., `campaign_service.py`)
- **Classes:** `PascalCase` (e.g., `Campaign`, `CampaignService`)
- **Functions/Variables:** `snake_case` (e.g., `create_campaign`, `max_events`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_ATTEMPTS`)

## Import Organization

All Python files use sorted imports in this order:
1. Standard library imports
2. Third-party imports (FastAPI, SQLAlchemy, etc.)
3. Local application imports (api, core, db, services)

Configured via `isort` in `pyproject.toml`.

## Testing

- **Framework:** pytest with pytest-asyncio
- **Location:** `tests/` directory
- **Fixtures:** Shared fixtures in `tests/conftest.py`
- **Test Client:** FastAPI TestClient for integration tests
- **Run:** `uv run pytest` or `pytest`

## Development Tools

- **Package Manager:** `uv` (recommended) or pip
- **Python Version:** 3.13+
- **Linting:** pylint (`.pylintrc`)
- **Type Checking:** Pyright (`pyrightconfig.json`)
- **Formatting:** isort for imports

## Running the Application

```bash
# Development server with auto-reload
uv run fastapi dev src/main.py

# Production server
uv run fastapi run src/main.py

# Install dependencies
uv sync

# Run tests
uv run pytest
```

## Future Enhancements

### Planned Improvements
1. **Repository Pattern** - Abstract database access into repository classes
2. **Dependency Injection** - Use FastAPI's DI for service layer
3. **Alembic Migrations** - Replace manual table creation
4. **Service Interfaces** - Define protocols for services
5. **Integration Tests** - Add tests for AWS scheduler integration
6. **Unit Tests** - Add comprehensive test coverage

### Scalability Considerations
- Service layer allows easy swap of implementations
- Database abstraction supports multiple backends
- Read-only external data access preserves source independence
- Scheduler abstraction allows APScheduler or AWS EventBridge

## Notes

- **Data Location:** Example data in `examples/data/`
- **Templates:** Located in `src/templates/` (referenced from `src/api/routes/basic.py`)
- **AWS Integration:** All AWS EventBridge operations handled by `core/scheduler.py`
