# Phase 1 Implementation Plan - Foundation

**Epic:** CMA-437 - Lilly | Echo
**Phase:** 1 of 6
**Estimated Duration:** 2-3 weeks
**Status:** Ready to Start

---

## Overview

Phase 1 establishes the foundational infrastructure for ECHO. By the end of this phase, we'll have a working Python project with FastAPI, database models, core data structures, configuration management, and a solid testing framework.

**What We're Building:**
- Modern Python project structure with `uv` package manager
- SQLAlchemy 2.0 database models (campaigns, cycles, records, notifications)
- Pydantic models for API validation and serialization
- Basic FastAPI application with health check endpoint
- Configuration management with environment variables
- Structured logging with context
- Unit test framework with pytest

**What We're NOT Building (Yet):**
- No API routes for campaigns/cycles (Phase 2)
- No data source connectors (Phase 2)
- No notification delivery (Phase 4)
- No AWS integrations (Phase 5)

---

## Success Criteria

Phase 1 is complete when:
- ✅ `make install` sets up the project successfully
- ✅ `make lint` passes with zero warnings
- ✅ `make type-check` passes with zero errors
- ✅ `make test` runs all unit tests successfully
- ✅ FastAPI app starts and responds to `/health` endpoint
- ✅ Database migrations run successfully
- ✅ All models are properly typed and validated

---

## Task Breakdown

### 1. Project Setup and Tooling

**Jira Story:** "Setup Python project structure and tooling"

**Files to Create:**
```
pyproject.toml           # Project configuration
uv.lock                  # Dependency lock file (auto-generated)
.gitignore               # Git ignore patterns
.pre-commit-config.yaml  # Pre-commit hooks
Makefile                 # Task automation
.env.example             # Environment variable template
README.md                # Project setup instructions
```

**Tasks:**
- Initialize `uv` project with Python 3.13+
- Configure dependencies:
  - FastAPI & uvicorn
  - SQLAlchemy 2.0 & asyncpg
  - Alembic (migrations)
  - Pydantic v2
  - structlog (logging)
  - pytest & pytest-asyncio & pytest-cov
  - ruff & mypy
- Configure ruff linting rules (PEP 8, type hints, etc.)
- Configure mypy strict mode
- Setup pre-commit hooks
- Create Makefile with common commands
- Update README with setup instructions

**Dependencies:**
```toml
[project]
name = "echo"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "asyncpg>=0.29.0",
    "alembic>=1.13.1",
    "pydantic>=2.6.0",
    "pydantic-settings>=2.1.0",
    "structlog>=24.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.4",
    "pytest-cov>=4.1.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
]
```

**Validation:**
- Run `uv sync` successfully
- Run `make lint` (should pass)
- Run `make type-check` (should pass with no errors)
- Pre-commit hooks install and run on commit

---

### 2. Project Structure

**Jira Story:** "Create foundational directory structure"

**Directory Structure:**
```
echo/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── health.py         # Health check endpoint
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Settings management
│   │   ├── logging.py            # Logging configuration
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── campaign.py       # Campaign Pydantic models
│   │       ├── cycle.py          # Cycle Pydantic models
│   │       ├── record.py         # Record Pydantic models
│   │       └── notification.py   # Notification Pydantic models
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py           # Database connection
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── base.py           # SQLAlchemy base
│   │       ├── campaign.py       # Campaign DB model
│   │       ├── cycle.py          # Cycle DB model
│   │       ├── record.py         # Record DB model
│   │       └── notification.py   # Notification DB model
│   └── main.py                   # FastAPI app entry
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_config.py
│   │   └── test_models.py
│   └── integration/
│       ├── __init__.py
│       └── test_health.py
├── scripts/
│   ├── __init__.py
│   └── init_db.py                # Database initialization
└── alembic/
    ├── env.py
    └── versions/                 # Migration files (auto-generated)
```

**Tasks:**
- Create all directories
- Create `__init__.py` files
- Create placeholder files with docstrings

**Validation:**
- All imports work (`from src.core.config import Settings`)
- No import errors when running `python -m src.main`

---

### 3. Configuration Management

**Jira Story:** "Implement configuration and environment management"

**Files:**
- `src/core/config.py` - Settings class
- `.env.example` - Template for environment variables

**Implementation:**
```python
# src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "ECHO"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://echo:password@localhost:5432/echo_dev"

    # AWS (for later phases)
    aws_region: str = "us-east-1"
    scheduler_group: str = "dev"

    # Logging
    log_level: str = "INFO"
    log_json: bool = False  # JSON in prod, console in dev

# Singleton instance
_settings: Settings | None = None

def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
```

**Environment Variables:**
```bash
# .env.example
# Application
APP_NAME=ECHO
APP_VERSION=0.1.0
DEBUG=true

# Database (local development)
DATABASE_URL=postgresql+asyncpg://echo:password@localhost:5432/echo_dev

# AWS (for later phases)
AWS_REGION=us-east-1
SCHEDULER_GROUP=dev

# Logging
LOG_LEVEL=INFO
LOG_JSON=false
```

**Tasks:**
- Implement Settings class with all config fields
- Add get_settings() function
- Create .env.example
- Write unit tests for config loading

**Validation:**
- Settings loads from environment variables
- Settings provides sensible defaults
- `get_settings()` returns singleton instance
- Tests verify config validation

---

### 4. Logging Setup

**Jira Story:** "Implement structured logging with structlog"

**Files:**
- `src/core/logging.py`

**Implementation:**
```python
# src/core/logging.py
import sys
import structlog
from src.core.config import get_settings

def setup_logging() -> None:
    """Configure structlog for the application."""
    settings = get_settings()

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_json:
        # JSON logging for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Console logging for development
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance."""
    return structlog.get_logger(name)
```

**Tasks:**
- Implement logging configuration
- Support JSON and console output modes
- Add log level configuration
- Write tests for logging setup

**Validation:**
- Logs output correctly in console mode (dev)
- Logs output as JSON when configured (prod)
- Log level filtering works
- Context variables are included in logs

---

### 5. Database Models (SQLAlchemy)

**Jira Story:** "Create SQLAlchemy database models"

**Files:**
- `src/db/models/base.py`
- `src/db/models/campaign.py`
- `src/db/models/cycle.py`
- `src/db/models/record.py`
- `src/db/models/notification.py`

**Base Model:**
```python
# src/db/models/base.py
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

class UUIDMixin:
    """Mixin for UUID primary key."""
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False
    )
```

**Campaign Model:**
```python
# src/db/models/campaign.py (simplified for Phase 1)
from sqlalchemy import String, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.models.base import Base, TimestampMixin, UUIDMixin

class Campaign(Base, UUIDMixin, TimestampMixin):
    """Campaign database model."""

    __tablename__ = "campaigns"

    # Basic fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Owner
    owner_email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Configuration (JSON fields)
    data_source: Mapped[dict] = mapped_column(JSON, nullable=False)
    campaign_schedule: Mapped[str] = mapped_column(String(100), nullable=False)
    escalation_rules: Mapped[list] = mapped_column(JSON, nullable=False)

    # Relationships
    cycles: Mapped[list["Cycle"]] = relationship(
        "Cycle",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
```

**Similar models for:**
- Cycle (status, start_date, end_date, stats)
- Record (object_id, source_data, verification_status)
- Notification (recipient, channel, status, sent_at)

**Tasks:**
- Create Base and Mixins
- Create all database models with proper relationships
- Add indexes for common queries
- Write unit tests for model creation

**Validation:**
- Models can be instantiated
- Relationships work correctly
- Type hints are correct
- No SQLAlchemy warnings

---

### 6. Pydantic Models

**Jira Story:** "Create Pydantic models for API validation"

**Files:**
- `src/core/models/campaign.py`
- `src/core/models/cycle.py`
- `src/core/models/record.py`
- `src/core/models/notification.py`

**Campaign Pydantic Models:**
```python
# src/core/models/campaign.py (simplified for Phase 1)
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr

class DataSourceConfig(BaseModel):
    """Data source configuration."""
    type: str = Field(..., description="Data source type (postgresql, api, etc.)")
    connection_parameter: str = Field(..., description="AWS Parameter Store parameter name")
    query: str = Field(..., description="SQL query or API endpoint")
    primary_key: str = Field(default="object_id", description="Primary key field name")

class EscalationRule(BaseModel):
    """Single escalation rule."""
    level: int = Field(..., ge=0, description="Escalation level (0-based)")
    delay_days: int = Field(..., ge=0, description="Days after previous escalation")
    recipients: list[str] = Field(..., min_length=1, description="Recipient field names")

class CampaignBase(BaseModel):
    """Base campaign fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    enabled: bool = Field(default=True)
    owner_email: EmailStr
    data_source: DataSourceConfig
    campaign_schedule: str = Field(..., description="AWS cron expression")
    escalation_rules: list[EscalationRule] = Field(..., min_length=1)

class CampaignCreate(CampaignBase):
    """Campaign creation request."""
    pass

class CampaignUpdate(BaseModel):
    """Campaign update request (all fields optional)."""
    name: str | None = None
    description: str | None = None
    enabled: bool | None = None
    owner_email: EmailStr | None = None
    # ... other optional fields

class CampaignResponse(CampaignBase):
    """Campaign response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

**Similar models for:**
- Cycle (CycleBase, CycleResponse)
- Record (RecordBase, RecordResponse)
- Notification (NotificationBase, NotificationResponse)

**Tasks:**
- Create all Pydantic models
- Add proper validation rules
- Add field descriptions for OpenAPI docs
- Write unit tests for validation

**Validation:**
- Models validate input correctly
- Invalid data raises ValidationError
- Field descriptions present
- Tests cover validation rules

---

### 7. Database Connection

**Jira Story:** "Setup database connection and session management"

**Files:**
- `src/db/database.py`
- `alembic.ini`
- `alembic/env.py`

**Database Connection:**
```python
# src/db/database.py
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)

def get_engine():
    """Create database engine."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

def get_session_factory():
    """Create session factory."""
    engine = get_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Alembic Setup:**
- Initialize Alembic
- Configure alembic.ini
- Configure alembic/env.py for async
- Create initial migration

**Tasks:**
- Implement database connection
- Setup Alembic for migrations
- Create initial migration with all tables
- Write script to initialize database

**Validation:**
- Database connection works
- `alembic upgrade head` creates all tables
- Session management works correctly
- Connection pooling configured

---

### 8. FastAPI Application

**Jira Story:** "Create basic FastAPI application with health check"

**Files:**
- `src/main.py`
- `src/api/routes/health.py`

**FastAPI App:**
```python
# src/main.py
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI
from src.api.routes import health
from src.core.config import get_settings
from src.core.logging import setup_logging, get_logger

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events."""
    settings = get_settings()
    logger = get_logger(__name__)

    # Startup
    logger.info("Starting ECHO application", version=settings.app_version)

    yield

    # Shutdown
    logger.info("Shutting down ECHO application")

def create_app() -> FastAPI:
    """Create FastAPI application."""
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise Campaign Handling and Orchestration",
        lifespan=lifespan,
    )

    # Register routes
    app.include_router(health.router, tags=["health"])

    return app

app = create_app()
```

**Health Check:**
```python
# src/api/routes/health.py
from fastapi import APIRouter, status
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str
    version: str

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Returns the health status of the service"
)
async def health_check() -> HealthResponse:
    """Health check endpoint for container orchestration."""
    from src.core.config import get_settings
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version
    )
```

**Tasks:**
- Create FastAPI app factory
- Add lifespan events
- Implement health check endpoint
- Write integration test for health endpoint

**Validation:**
- App starts successfully: `uvicorn src.main:app`
- Health endpoint responds: `curl http://localhost:8000/health`
- OpenAPI docs available: `http://localhost:8000/docs`

---

### 9. Testing Framework

**Jira Story:** "Setup pytest and write initial tests"

**Files:**
- `tests/conftest.py`
- `tests/unit/test_config.py`
- `tests/unit/test_models.py`
- `tests/integration/test_health.py`

**Pytest Configuration:**
```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import create_app

@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    return create_app()

@pytest.fixture
async def client(app):
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
```

**Example Tests:**
```python
# tests/unit/test_config.py
from src.core.config import Settings, get_settings

def test_settings_loads_defaults():
    """Test settings with default values."""
    settings = Settings()
    assert settings.app_name == "ECHO"
    assert settings.debug is False

def test_get_settings_singleton():
    """Test get_settings returns singleton."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2

# tests/integration/test_health.py
import pytest

@pytest.mark.asyncio
async def test_health_endpoint(client):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ECHO"
```

**Tasks:**
- Configure pytest with asyncio support
- Create test fixtures
- Write unit tests for config and models
- Write integration test for health endpoint
- Configure coverage reporting

**Validation:**
- `make test` runs all tests successfully
- `make test-cov` shows coverage report
- All tests pass
- Coverage > 80% for core modules

---

### 10. Makefile and Scripts

**Jira Story:** "Create Makefile and helper scripts"

**Files:**
- `Makefile`
- `scripts/init_db.py`

**Makefile:**
```makefile
.PHONY: help install lint format type-check test test-cov run dev clean db-init

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
	uv run uvicorn src.main:app --host 0.0.0.0 --port 8000

dev:  ## Run development server with auto-reload
	uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

db-init:  ## Initialize database (run migrations)
	uv run alembic upgrade head

clean:  ## Clean up generated files
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +
```

**Database Init Script:**
```python
# scripts/init_db.py
"""Initialize database with tables."""
import asyncio
from src.db.database import get_engine
from src.db.models.base import Base
from src.core.logging import setup_logging, get_logger

async def init_db():
    """Create all tables."""
    setup_logging()
    logger = get_logger(__name__)

    engine = get_engine()

    logger.info("Creating database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")

if __name__ == "__main__":
    asyncio.run(init_db())
```

**Tasks:**
- Create Makefile with all commands
- Create database initialization script
- Test all Makefile targets
- Update README with usage instructions

**Validation:**
- All Makefile targets work
- `make help` shows all commands
- Scripts execute successfully

---

## Jira Story Breakdown

Create these stories under Epic CMA-437:

1. **CMA-XXX: Setup Python project structure and tooling**
   - Estimate: 2 story points
   - Tasks: pyproject.toml, dependencies, linting, pre-commit

2. **CMA-XXX: Create foundational directory structure**
   - Estimate: 1 story point
   - Tasks: Create all directories and placeholder files

3. **CMA-XXX: Implement configuration and environment management**
   - Estimate: 2 story points
   - Tasks: Settings class, environment variables, tests

4. **CMA-XXX: Implement structured logging with structlog**
   - Estimate: 2 story points
   - Tasks: Logging setup, JSON/console modes, tests

5. **CMA-XXX: Create SQLAlchemy database models**
   - Estimate: 5 story points
   - Tasks: Base, Campaign, Cycle, Record, Notification models

6. **CMA-XXX: Create Pydantic models for API validation**
   - Estimate: 5 story points
   - Tasks: Campaign, Cycle, Record, Notification Pydantic models

7. **CMA-XXX: Setup database connection and session management**
   - Estimate: 3 story points
   - Tasks: Database connection, Alembic setup, migrations

8. **CMA-XXX: Create basic FastAPI application with health check**
   - Estimate: 2 story points
   - Tasks: FastAPI app, lifespan, health endpoint

9. **CMA-XXX: Setup pytest and write initial tests**
   - Estimate: 3 story points
   - Tasks: Test fixtures, unit tests, integration tests

10. **CMA-XXX: Create Makefile and helper scripts**
    - Estimate: 1 story point
    - Tasks: Makefile, database init script

**Total: 26 story points**

---

## Dependencies

### External
- PostgreSQL 15+ (local or AWS RDS)
- Python 3.13+
- uv package manager

### Python Packages
- FastAPI & uvicorn
- SQLAlchemy 2.0 & asyncpg
- Alembic
- Pydantic v2
- structlog
- pytest & pytest-asyncio & pytest-cov
- ruff & mypy

---

## Risk Assessment

**Low Risk:**
- Standard Python setup
- Well-documented libraries
- No complex business logic yet

**Potential Issues:**
- Async/await patterns (if unfamiliar)
- SQLAlchemy 2.0 syntax changes from 1.x
- Type hints strictness with mypy

**Mitigation:**
- Follow implementation examples above
- Reference official documentation
- Ask for help if stuck on async patterns

---

## Testing Strategy

**Unit Tests:**
- Configuration loading
- Pydantic model validation
- Database model instantiation
- Utility functions

**Integration Tests:**
- FastAPI health endpoint
- Database connection
- End-to-end app startup

**Coverage Target:** > 80% for all core modules

---

## Completion Checklist

Before marking Phase 1 complete:

- [ ] All dependencies installed (`make install`)
- [ ] All linting passes (`make lint`)
- [ ] All type checking passes (`make type-check`)
- [ ] All tests pass (`make test`)
- [ ] Coverage > 80% (`make test-cov`)
- [ ] FastAPI app starts (`make dev`)
- [ ] Health endpoint responds (`curl localhost:8000/health`)
- [ ] Database migrations run (`make db-init`)
- [ ] All Jira stories closed
- [ ] README updated with setup instructions
- [ ] Code committed and pushed to git

---

## Next Phase Preview

**Phase 2: Campaign Management**
- Campaign CRUD API endpoints
- Campaign service layer
- PostgreSQL data source connector
- EventBridge scheduler integration
- Campaign validation logic

Phase 2 will build on the foundation established in Phase 1.

---

## Questions Before Starting?

1. Do you have PostgreSQL available locally or should we use Docker?
2. Do you want to use AWS RDS from the start or local Postgres for Phase 1?
3. Any preferences on database name (`echo_dev` ok)?
4. Should we create all Jira stories now or as we go?

---

**Ready to begin? When you're ready to start, just say:**
- "Start Phase 1" or
- "Create Jira stories for Phase 1" or
- "Let's begin with task 1"
