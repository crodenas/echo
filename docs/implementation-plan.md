# Implementation Plan

This document outlines the technical approach and development roadmap for ECHO.

## Technology Stack

### Backend Framework
- **FastAPI** - Modern, fast web framework with automatic API documentation
- **Python 3.13+** - Latest Python with improved performance and type hints
- **uvicorn** - ASGI server for production deployment
- **Pydantic v2** - Data validation and serialization

### Database
- **PostgreSQL 15+** - Primary data store
- **SQLAlchemy 2.0** - ORM with async support
- **Alembic** - Database migrations
- **asyncpg** - Async PostgreSQL driver

### Scheduling
- **APScheduler** - In-process scheduler (development)
- **AWS EventBridge Scheduler** - Distributed scheduler (production)
- **aws-croniter** - AWS cron expression parsing

### Notification Channels
- **boto3** - AWS SES for email
- **aiohttp** - Async HTTP client for webhooks
- **Microsoft Graph SDK** - Teams integration
- **Slack SDK** - Slack integration

### Template Engine
- **Jinja2** - HTML and text template rendering

### Package Management
- **uv** - Fast, modern Python package manager
- **pyproject.toml** - Modern Python project configuration

### Code Quality
- **ruff** - Fast Python linter and formatter (replaces flake8, black, isort)
- **mypy** - Static type checking
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Code coverage

### Development Tools
- **pre-commit** - Git hooks for code quality
- **Makefile** - Common task automation

## Project Structure

```
echo/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # CI/CD pipeline
│       └── deploy.yml                # Deployment workflow
├── docs/                             # Documentation (current folder)
├── examples/                         # Example data
│   └── data/                         # Sample JSON files
├── src/
│   ├── api/                          # API layer
│   │   ├── routes/
│   │   │   ├── campaigns.py          # Campaign CRUD endpoints
│   │   │   ├── cycles.py             # Cycle management endpoints
│   │   │   ├── notifications.py      # Notification endpoints
│   │   │   └── health.py             # Health check endpoints
│   │   └── dependencies.py           # FastAPI dependencies
│   ├── core/                         # Core business logic
│   │   ├── models/
│   │   │   ├── campaign.py           # Campaign Pydantic models
│   │   │   ├── cycle.py              # Cycle Pydantic models
│   │   │   ├── record.py             # Record Pydantic models
│   │   │   └── notification.py       # Notification Pydantic models
│   │   ├── config.py                 # Configuration management
│   │   └── logging.py                # Logging configuration
│   ├── db/                           # Database layer
│   │   ├── models/
│   │   │   ├── campaign.py           # Campaign SQLAlchemy model
│   │   │   ├── cycle.py              # Cycle SQLAlchemy model
│   │   │   ├── record.py             # Record SQLAlchemy model
│   │   │   └── notification.py       # Notification SQLAlchemy model
│   │   ├── database.py               # Database connection and session
│   │   └── migrations/               # Alembic migrations
│   ├── services/                     # Service layer
│   │   ├── campaign_service.py       # Campaign business logic
│   │   ├── cycle_service.py          # Cycle execution logic
│   │   ├── notification_service.py   # Notification delivery
│   │   └── data_source_service.py    # Data source integration
│   ├── integrations/                 # External integrations
│   │   ├── data_sources/
│   │   │   ├── base.py               # DataSource protocol
│   │   │   ├── sql.py                # SQL data source
│   │   │   ├── api.py                # REST API data source
│   │   │   └── http.py               # HTTP endpoint data source
│   │   ├── notifications/
│   │   │   ├── base.py               # NotificationChannel protocol
│   │   │   ├── email.py              # Email channel (SES)
│   │   │   ├── teams.py              # Microsoft Teams
│   │   │   └── slack.py              # Slack
│   │   └── schedulers/
│   │       ├── base.py               # Scheduler protocol
│   │       ├── apscheduler.py        # APScheduler implementation
│   │       └── eventbridge.py        # AWS EventBridge implementation
│   ├── templates/                    # Jinja2 templates
│   │   ├── email/
│   │   │   ├── default.html          # Default email template
│   │   │   └── default.txt           # Plain text fallback
│   │   ├── teams/
│   │   │   └── default.json          # Teams card template
│   │   └── slack/
│   │       └── default.json          # Slack block template
│   ├── utils/                        # Utility modules
│   │   ├── verification.py           # Verification detection logic
│   │   ├── grouping.py               # Notification grouping
│   │   └── aws_cron.py               # AWS cron utilities
│   └── main.py                       # FastAPI application entry
├── tests/
│   ├── unit/                         # Unit tests
│   ├── integration/                  # Integration tests
│   ├── fixtures/                     # Test fixtures
│   └── conftest.py                   # Pytest configuration
├── scripts/
│   ├── init_db.py                    # Database initialization
│   ├── seed_data.py                  # Seed example data
│   └── migrate.py                    # Migration runner
├── .env.example                      # Environment variables template
├── .gitignore
├── .pre-commit-config.yaml           # Pre-commit hooks
├── Makefile                          # Task automation
├── pyproject.toml                    # Project configuration
├── uv.lock                           # Dependency lock file
├── README.md
└── CLAUDE.md
```

## Code Standards

### PEP Compliance

**PEP 8 - Style Guide:**
- Line length: 88 characters (Black default, also Ruff default)
- Indentation: 4 spaces
- Imports: Grouped and sorted (stdlib, third-party, local)
- Naming conventions:
  - `snake_case` for functions, variables, modules
  - `PascalCase` for classes
  - `UPPER_SNAKE_CASE` for constants
  - `_leading_underscore` for private members

**PEP 484 - Type Hints:**
- All function signatures must have type hints
- Use modern type syntax: `str | None` instead of `Optional[str]`
- Use `list[str]` instead of `List[str]` (Python 3.9+)
- Complex types in separate type aliases

**PEP 257 - Docstrings:**
- Google-style docstrings for all public APIs
- One-line summary for simple functions
- Detailed docs for complex functions

**Example:**
```python
"""Campaign service module.

This module provides business logic for campaign management including
creation, updates, scheduling, and lifecycle management.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.campaign import Campaign, CampaignCreate
from src.db.models.campaign import Campaign as CampaignDB


async def create_campaign(
    session: AsyncSession,
    campaign_data: CampaignCreate,
    created_by: str,
) -> Campaign:
    """Create a new campaign with validation and scheduler setup.

    Args:
        session: Database session for transaction management.
        campaign_data: Campaign configuration and settings.
        created_by: User or system that created the campaign.

    Returns:
        Created campaign with assigned ID and timestamps.

    Raises:
        ValueError: If campaign configuration is invalid.
        SchedulerError: If scheduler setup fails.
    """
    # Implementation
    ...
```

### Linting and Formatting

**Ruff Configuration (pyproject.toml):**
```toml
[tool.ruff]
target-version = "py313"
line-length = 88

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "ANN", # flake8-annotations
    "B",   # flake8-bugbear
    "A",   # flake8-builtins
    "C4",  # flake8-comprehensions
    "DTZ", # flake8-datetimez
    "T20", # flake8-print
    "SIM", # flake8-simplify
]
ignore = [
    "ANN101", # Missing type annotation for self
    "ANN102", # Missing type annotation for cls
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["ANN"]  # No type hints required in tests
```

**Mypy Configuration:**
```toml
[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
plugins = ["pydantic.mypy"]
```

### Pre-commit Hooks

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, sqlalchemy]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
```

## Development Workflow

### Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone <repo-url>
cd echo

# Create virtual environment and install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Setup database
make db-setup

# Run migrations
make db-migrate

# Seed example data
make db-seed
```

### Makefile Targets

```makefile
.PHONY: help install lint format type-check test test-cov run dev db-setup db-migrate db-seed clean

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	uv sync

lint:  ## Run linter
	uv run ruff check .

format:  ## Format code
	uv run ruff format .

type-check:  ## Run type checker
	uv run mypy src

test:  ## Run tests
	uv run pytest

test-cov:  ## Run tests with coverage
	uv run pytest --cov=src --cov-report=html --cov-report=term

run:  ## Run production server
	uv run fastapi run src/main.py

dev:  ## Run development server with auto-reload
	uv run fastapi dev src/main.py

db-setup:  ## Initialize database
	uv run python scripts/init_db.py

db-migrate:  ## Run database migrations
	uv run alembic upgrade head

db-seed:  ## Seed example data
	uv run python scripts/seed_data.py

clean:  ## Clean up generated files
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
```

## Testing Strategy

### Unit Tests
- Test individual functions and classes in isolation
- Mock external dependencies (database, schedulers, APIs)
- Fast execution (< 1 second per test)
- High coverage target (>80%)

### Integration Tests
- Test component interactions (service + database)
- Use test database (PostgreSQL in Docker)
- Test API endpoints with TestClient
- Moderate execution time

### End-to-End Tests
- Test complete workflows (campaign creation → cycle execution → notification)
- Use all real components (database, scheduler)
- Mock only external services (SES, Teams API)
- Run in CI/CD before deployment

### Test Organization

```python
# tests/unit/services/test_campaign_service.py
import pytest
from unittest.mock import AsyncMock

from src.services.campaign_service import create_campaign


@pytest.mark.asyncio
async def test_create_campaign_success(mock_db_session, sample_campaign_data):
    """Test successful campaign creation."""
    result = await create_campaign(
        session=mock_db_session,
        campaign_data=sample_campaign_data,
        created_by="test@example.com"
    )

    assert result.name == sample_campaign_data.name
    assert result.enabled is True
    mock_db_session.add.assert_called_once()
```

## Deployment Strategy

### Development
- Local environment with PostgreSQL in Docker
- APScheduler for scheduling
- Email via local SMTP server (MailHog)
- Hot reload for rapid iteration

### Staging
- AWS ECS Fargate
- RDS PostgreSQL
- EventBridge Scheduler
- SES for emails (sandbox mode)

### Production
- AWS ECS Fargate (multi-AZ)
- RDS PostgreSQL (Multi-AZ)
- EventBridge Scheduler
- SES for emails (production mode)
- CloudWatch monitoring and alarms

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: make lint
      - run: make type-check
      - run: make test-cov
```

## Implementation Phases

### Phase 1: Foundation (2-3 weeks)
- [ ] Project setup (uv, pyproject.toml, Makefile)
- [ ] Database models and migrations
- [ ] Core Pydantic models
- [ ] Basic FastAPI app structure
- [ ] Configuration management
- [ ] Logging setup
- [ ] Unit test framework

### Phase 2: Campaign Management (2 weeks)
- [ ] Campaign CRUD API endpoints
- [ ] Campaign service layer
- [ ] Data source connectors (SQL, API, HTTP)
- [ ] Basic scheduler integration (APScheduler)
- [ ] Campaign validation logic
- [ ] Integration tests

### Phase 3: Cycle Execution (3 weeks)
- [ ] Cycle creation and management
- [ ] Data ingestion pipeline
- [ ] Verification detection logic
- [ ] Record management
- [ ] Escalation engine
- [ ] Notification queue builder

### Phase 4: Notification System (2 weeks)
- [ ] Email channel (SES)
- [ ] Template rendering
- [ ] Notification delivery
- [ ] Retry logic
- [ ] Delivery tracking
- [ ] Additional channels (Teams, Slack)

### Phase 5: Production Readiness (2 weeks)
- [ ] AWS EventBridge integration
- [ ] Error handling and monitoring
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Deployment automation
- [ ] Performance optimization

### Phase 6: Polish & Launch (1 week)
- [ ] UI for campaign management
- [ ] Audit logging
- [ ] Reporting and dashboards
- [ ] Final testing
- [ ] Production deployment
