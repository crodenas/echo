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
- **AWS EventBridge Scheduler** - All environments (dev, prod)
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
│       ├── deploy-api.yml            # Deploy API service
│       └── deploy-worker.yml         # Deploy cycle worker task definition
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
│   │   ├── data_source_service.py    # Data source integration
│   │   └── parameters_service.py     # AWS Parameter Store operations
│   ├── integrations/                 # External integrations
│   │   ├── data_sources/
│   │   │   ├── base.py               # DataSource protocol
│   │   │   └── postgresql.py         # PostgreSQL data source (MVP)
│   │   │   # Future: api.py, mysql.py, http.py
│   │   ├── notifications/
│   │   │   ├── base.py               # NotificationChannel protocol
│   │   │   ├── email.py              # Email channel (SES)
│   │   │   ├── teams.py              # Microsoft Teams
│   │   │   └── slack.py              # Slack
│   │   └── schedulers/
│   │       ├── base.py               # Scheduler protocol
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

**Development Environment:** Single developer, uses dev AWS account

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

# Configure environment (connects to AWS dev resources)
cat > .env <<EOF
# Database (AWS RDS dev instance)
DATABASE_URL=postgresql+asyncpg://echo:password@echo-dev.rds.amazonaws.com:5432/echo_dev

# Scheduler (AWS EventBridge dev group)
SCHEDULER_GROUP=dev
AWS_REGION=us-east-1

# Azure AD (dev app registration)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-dev-client-id
AZURE_CLIENT_SECRET=your-dev-client-secret

# AWS credentials (for EventBridge access)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
EOF

# Run migrations (against AWS RDS)
uv run alembic upgrade head

# Seed example data (optional)
uv run python scripts/seed_data.py

# Run API locally (connects to AWS RDS + EventBridge)
uv run fastapi dev src/main.py
```

**Infrastructure Required:**
- AWS RDS PostgreSQL instance (echo-dev)
- AWS IAM credentials with EventBridge Scheduler permissions
- Azure AD app registration (echo-dev)

**Note:** API runs locally but uses AWS resources (RDS, EventBridge). No local containers needed.

### Makefile Targets

```makefile
.PHONY: help install lint format type-check test test-cov run dev db-migrate db-seed clean

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

### Containerized Execution Model

**Design Principle: Isolation**
- Each cycle escalation runs in its own container (on-demand)
- Failures in one campaign/cycle do not impact others
- Bad data sources, template errors, or crashes are isolated
- Clear failure boundaries and independent retry logic

**Architecture: Hybrid Approach**

**Component 1: Long-Running API Service**
```
ECS Service (always running)
- FastAPI web server
- Campaign CRUD operations
- User interface
- Creates EventBridge schedules
- Handles: /api/campaigns, /internal/start-cycle
- Instances: 1-3 (auto-scaling)
- Resources: 256 CPU, 512 MB RAM
```

**Component 2: On-Demand Cycle Workers**
```
ECS Fargate Tasks (ephemeral)
- Triggered by: EventBridge schedules
- Processes: One escalation per container
- Lifecycle: Spin up → Process → Terminate
- Instances: As many as needed (concurrent escalations)
- Resources: 1024 CPU, 2048 MB RAM
```

### Cycle Execution Flow

```
EventBridge Campaign Schedule (Recurring)
  ↓
Triggers: API Service POST /internal/start-cycle/{campaign_id}
  ↓
API Service (quick):
  1. Create Cycle record in DB
  2. Create EventBridge schedules (one-time):
     - cycle-123-esc-1 → ECS Task (immediate)
     - cycle-123-esc-2 → ECS Task (+7 days)
     - cycle-123-esc-3 → ECS Task (+14 days)
  3. Return success
  ↓
(API service continues serving other requests)

...7 days later...

EventBridge Escalation Schedule Triggers
  ↓
Launches: NEW Fargate Task
  ↓
Worker Container:
  1. Load cycle + campaign from DB
  2. Query data source
  3. Filter records by mode
  4. Check verification status
  5. Send notifications
  6. Update cycle stats
  7. Terminate
  ↓
Container destroyed (logs in CloudWatch)
```

### Isolation Benefits

**Scenario 1: Bad Data Source**
```
Campaign A → Container 1 ✅ (Success)
Campaign B → Container 2 💥 (Data source timeout)
Campaign C → Container 3 ✅ (Unaffected by B's failure!)
```

**Scenario 2: Template Error**
```
Cycle X, Escalation 1 → Container 1 ✅ (Success)
Cycle X, Escalation 2 → Container 2 💥 (Template syntax error)
Cycle X, Escalation 3 → Container 3 ✅ (Still runs after retry!)
```

**Scenario 3: Memory Exhaustion**
```
Small Cycle (100 records) → Container 1 ✅ (500 MB used)
Huge Cycle (10k records) → Container 2 💥 (OOM killed)
Other Cycles → Containers 3,4,5 ✅ (Unaffected!)
```

### Development
- API runs locally (FastAPI dev server with hot reload)
- AWS RDS PostgreSQL (echo-dev instance)
- AWS EventBridge Scheduler (dev schedule group)
- AWS SES for emails (sandbox mode)
- Worker containers: Test locally or deploy to ECS dev
- Single developer environment

### Staging (Optional)
- AWS ECS Fargate
  - Service: echo-api (1 instance)
  - Task Definition: echo-cycle-worker (on-demand)
- RDS PostgreSQL (echo-staging instance)
- EventBridge Scheduler (staging group)
- SES for emails (sandbox mode)

### Production
- AWS ECS Fargate (multi-AZ)
  - Service: echo-api (2-3 instances, auto-scaling)
  - Task Definition: echo-cycle-worker (on-demand, concurrent)
- RDS PostgreSQL (Multi-AZ)
- EventBridge Scheduler (prod group)
- SES for emails (production mode)
- CloudWatch monitoring and alarms
- Dead Letter Queue for failed escalations

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

## Secret Management

### AWS Systems Manager Parameter Store

**Decision:** Use Parameter Store (SecureString) for database connection strings.

**Why Parameter Store:**
- ✅ **FREE** for up to 10,000 parameters (vs $0.40/month per secret)
- ✅ KMS encryption (same security as Secrets Manager)
- ✅ Versioning and tagging support
- ✅ Simple parameter naming (`/echo/campaigns/{id}/connection`)
- ✅ No automatic rotation needed (users manage DB passwords)

**How It Works:**
1. User creates campaign, provides connection string via API
2. ECHO creates SecureString parameter in Parameter Store
3. ECHO stores parameter name (not connection string) in database
4. At runtime, ECHO fetches connection string from Parameter Store
5. Connection strings never stored in ECHO's database

**Implementation:**
```python
# src/services/parameters_service.py

import boto3
from functools import lru_cache

ssm_client = boto3.client('ssm')

async def create_connection_parameter(
    campaign_id: str,
    connection_string: str,
    created_by: str
) -> str:
    """Create parameter in AWS Systems Manager Parameter Store.

    Returns: parameter name (e.g., "/echo/campaigns/campaign-123/connection")
    """

    parameter_name = f"/echo/campaigns/{campaign_id}/connection"

    ssm_client.put_parameter(
        Name=parameter_name,
        Description=f"Data source connection for campaign {campaign_id}",
        Value=connection_string,
        Type='SecureString',  # Encrypted with KMS
        Tags=[
            {"Key": "CampaignId", "Value": campaign_id},
            {"Key": "CreatedBy", "Value": created_by},
            {"Key": "ManagedBy", "Value": "ECHO"}
        ]
    )

    return parameter_name


@lru_cache(maxsize=100)
def get_connection_string(parameter_name: str) -> str:
    """Fetch connection string from Parameter Store (cached).

    Cached for 5 minutes to reduce API calls.
    """

    response = ssm_client.get_parameter(
        Name=parameter_name,
        WithDecryption=True  # Decrypt using KMS
    )

    return response['Parameter']['Value']


async def update_connection_parameter(parameter_name: str, connection_string: str):
    """Update existing parameter with new connection string."""

    ssm_client.put_parameter(
        Name=parameter_name,
        Value=connection_string,
        Type='SecureString',
        Overwrite=True
    )

    # Clear cache
    get_connection_string.cache_clear()


async def delete_connection_parameter(parameter_name: str):
    """Delete parameter from Parameter Store."""

    ssm_client.delete_parameter(Name=parameter_name)

    # Clear cache
    get_connection_string.cache_clear()
```

**IAM Permissions Required:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:PutParameter",
        "ssm:GetParameter",
        "ssm:DeleteParameter"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/echo/campaigns/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:Encrypt"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Data Source Connectors

### MVP: PostgreSQL Only

**Decision:** Start with a single, well-tested connector rather than multiple half-built ones.

**PostgreSQL Connector:**
```python
# src/integrations/data_sources/base.py

from typing import Protocol

class DataSource(Protocol):
    """Data source interface for fetching records."""

    async def fetch_records(self) -> list[dict]:
        """Fetch all records from data source."""
        ...

    async def get_record(self, object_id: str) -> dict | None:
        """Fetch single record by ID."""
        ...

# src/integrations/data_sources/postgresql.py

import asyncpg
from src.services.parameters_service import get_connection_string

class PostgreSQLDataSource:
    """PostgreSQL data source connector.

    Executes a SQL query against a PostgreSQL database and
    returns results as records for ECHO processing.

    Connection string is fetched from AWS Parameter Store at runtime.
    """

    def __init__(self, config: dict):
        self.connection_parameter = config["connection_parameter"]  # Parameter name, not connection string
        self.query = config["query"]
        self.primary_key = config.get("primary_key", "object_id")

    async def fetch_records(self) -> list[dict]:
        """Execute query and return all records."""

        # Fetch connection string from Parameter Store (cached)
        connection_string = get_connection_string(self.connection_parameter)

        conn = await asyncpg.connect(connection_string)

        try:
            rows = await conn.fetch(self.query)
            return [dict(row) for row in rows]
        finally:
            await conn.close()

    async def get_record(self, object_id: str) -> dict | None:
        """Fetch single record by primary key."""

        connection_string = get_connection_string(self.connection_parameter)

        conn = await asyncpg.connect(connection_string)

        try:
            query = f"{self.query} WHERE {self.primary_key} = $1"
            row = await conn.fetchrow(query, object_id)
            return dict(row) if row else None
        finally:
            await conn.close()
```

**Campaign Configuration (as stored in database):**
```python
{
  "name": "Service Verification",

  "data_source": {
    "type": "postgresql",
    "connection_parameter": "/echo/campaigns/campaign-123/connection",  # Parameter name (not connection string!)
    "query": """
      SELECT
        service_id as object_id,
        service_name as name,
        primary_owner as primary_owner,
        tech_lead as tech_lead,
        description,
        last_updated,
        environment
      FROM services
      WHERE active = true
    """,
    "primary_key": "object_id"
  }
}
```

**Campaign Creation API (user provides connection string):**
```python
# POST /api/campaigns
{
  "name": "Service Verification",

  "data_source": {
    "type": "postgresql",
    "connection_string": "postgresql://user:pass@host:5432/dbname",  # User provides once
    "query": "SELECT ..."
  }
}

# ECHO automatically:
# 1. Creates parameter in Parameter Store
# 2. Stores parameter name (not connection string) in database
# 3. Returns campaign (without connection string)
```
```

**Example Data Source Views:**

```sql
-- Service verification
CREATE VIEW echo_services_view AS
SELECT
  service_id as object_id,
  service_name as name,
  primary_owner,
  tech_lead,
  product_owner,
  last_verified,
  last_updated,
  environment,
  criticality
FROM services
WHERE active = true;

-- Database verification
CREATE VIEW echo_databases_view AS
SELECT
  db_instance_id as object_id,
  db_name as name,
  dba_owner,
  app_owner,
  last_audit_date as last_verified,
  environment
FROM databases
WHERE status = 'active';
```

**Benefits of PostgreSQL First:**
- ✅ Most common enterprise database
- ✅ ECHO itself uses PostgreSQL (dogfooding)
- ✅ Well-defined query interface (SQL)
- ✅ Easy to create views for data sources
- ✅ Strong typing and validation
- ✅ Can connect to most systems via foreign data wrappers

**Post-MVP Data Sources:**
- MySQL/MariaDB connector
- REST API connector
- GraphQL connector
- CSV/file-based connector
- Snowflake/data warehouse connector

---

## Campaign API with Automatic Secret Management

### Create Campaign (with automatic parameter creation)

```python
# src/api/routes/campaigns.py

from src.services.parameters_service import create_connection_parameter

@app.post("/api/campaigns")
async def create_campaign(
    campaign: CampaignCreate,
    user = Depends(get_current_user)
):
    """Create campaign with automatic secret management.

    User provides connection string once.
    ECHO creates parameter in Parameter Store and stores parameter name.
    Connection string never persisted in ECHO's database.
    """

    # 1. Validate connection string is provided
    if not campaign.data_source.connection_string:
        raise HTTPException(400, "connection_string required for PostgreSQL data source")

    # 2. Create campaign record (to get ID)
    db_campaign = Campaign(
        name=campaign.name,
        owner_email=user["email"],
        created_by=user["email"],
        escalation_rules=campaign.escalation_rules,
        # ... other fields
    )
    db.add(db_campaign)
    await db.flush()  # Get campaign ID

    # 3. Create parameter in AWS Parameter Store
    parameter_name = await create_connection_parameter(
        campaign_id=str(db_campaign.id),
        connection_string=campaign.data_source.connection_string,
        created_by=user["email"]
    )

    # 4. Store parameter name (NOT connection string) in database
    db_campaign.data_source = {
        "type": campaign.data_source.type,
        "connection_parameter": parameter_name,  # Only parameter name stored!
        "query": campaign.data_source.query,
        "primary_key": campaign.data_source.primary_key
    }

    await db.commit()
    await db.refresh(db_campaign)

    return db_campaign


@app.put("/api/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    updates: CampaignUpdate,
    user = Depends(get_current_user)
):
    """Update campaign, optionally updating connection string."""

    campaign = await get_campaign(campaign_id)

    # Check ownership
    if campaign.owner_email != user["email"] and "echo.admin" not in user["roles"]:
        raise HTTPException(403, "Not authorized")

    # If connection string is being updated
    if updates.data_source and updates.data_source.connection_string:
        await update_connection_parameter(
            parameter_name=campaign.data_source["connection_parameter"],
            connection_string=updates.data_source.connection_string
        )

    # Update other fields
    if updates.name:
        campaign.name = updates.name
    if updates.escalation_rules:
        campaign.escalation_rules = updates.escalation_rules
    # ... other fields

    await db.commit()
    return campaign


@app.delete("/api/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    user = Depends(require_role("echo.admin"))
):
    """Delete campaign and clean up parameter."""

    campaign = await get_campaign(campaign_id)

    # Delete parameter from Parameter Store
    await delete_connection_parameter(
        parameter_name=campaign.data_source["connection_parameter"]
    )

    # Delete campaign from database
    db.delete(campaign)
    await db.commit()

    return {"status": "deleted"}
```

### Pydantic Models

```python
# src/core/models/campaign.py

class DataSourceCreate(BaseModel):
    """Data source configuration (user provides connection string)."""
    type: Literal["postgresql"]
    connection_string: str  # User provides this (not stored)
    query: str
    primary_key: str = "object_id"

class DataSourceStored(BaseModel):
    """Data source configuration (stored in database)."""
    type: Literal["postgresql"]
    connection_parameter: str  # Parameter Store name (stored)
    query: str
    primary_key: str = "object_id"

class CampaignCreate(BaseModel):
    name: str
    data_source: DataSourceCreate  # User provides connection_string
    escalation_rules: list

class CampaignResponse(BaseModel):
    id: str
    name: str
    data_source: DataSourceStored  # Response has parameter name (not connection_string)
    escalation_rules: list
```

## Implementation Phases

**Note:** ECHO is **API-first**. All functionality is exposed via REST API. A minimal management UI is in scope for later phases (Phase 6) but is optional - the system is fully functional via API alone.

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
- [ ] **PostgreSQL data source connector (MVP - single connector)**
- [ ] EventBridge scheduler integration
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
- [ ] Minimal management UI (optional)
  - [ ] Campaign list/create/edit
  - [ ] Cycle status viewer
  - [ ] Notification history
  - [ ] Simple HTML templates (FastAPI + Jinja2) or SPA
- [ ] Verification API and simple verification page
- [ ] Audit logging
- [ ] Reporting and dashboards
- [ ] Final testing
- [ ] Production deployment

## Container Configuration

### Dockerfile (Multi-Stage Build)

```dockerfile
# Base stage
FROM python:3.13-slim as base
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# API Service stage
FROM base as api
COPY src/ ./src/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Cycle Worker stage
FROM base as worker
COPY src/ ./src/
ENV MODE=worker
CMD ["python", "-m", "src.workers.cycle_worker"]
```

### Local Development

**No Docker Compose needed.** Developer runs API locally and connects to AWS resources:

```bash
# Run API locally (with hot reload)
uv run fastapi dev src/main.py

# API connects to:
# - AWS RDS (echo-dev) for database
# - AWS EventBridge (dev group) for schedules
# - AWS SES for emails
```

**Worker Testing:**
```bash
# Test worker locally
CYCLE_ID=cycle-123 ESCALATION_LEVEL=1 uv run python -m src.workers.cycle_worker

# Or deploy worker to ECS dev and trigger via EventBridge
```

### EventBridge → ECS Task Configuration

```python
# src/integrations/schedulers/eventbridge.py

def create_escalation_schedule(cycle_id: str, escalation_level: int, trigger_time: datetime):
    """Create one-time schedule that launches ECS Fargate Task."""
    
    schedule_name = f"cycle-{cycle_id}-esc-{escalation_level}"
    
    client.create_schedule(
        Name=schedule_name,
        GroupName=settings.scheduler_group,
        
        # One-time trigger
        ScheduleExpression=f"at({trigger_time.isoformat()})",
        ScheduleExpressionTimezone="UTC",
        
        # Launch ECS Fargate Task
        Target={
            "Arn": settings.ecs_cluster_arn,
            "RoleArn": settings.ecs_events_role_arn,
            "EcsParameters": {
                "TaskDefinitionArn": settings.cycle_worker_task_arn,
                "LaunchType": "FARGATE",
                "NetworkConfiguration": {
                    "awsvpcConfiguration": {
                        "Subnets": settings.ecs_subnets,
                        "SecurityGroups": settings.ecs_security_groups,
                        "AssignPublicIp": "ENABLED"
                    }
                },
                "PlatformVersion": "LATEST",
                "TaskCount": 1,
                "EnableExecuteCommand": False,
                
                # Pass cycle info to container
                "Overrides": {
                    "ContainerOverrides": [{
                        "Name": "echo-worker",
                        "Environment": [
                            {"Name": "CYCLE_ID", "Value": cycle_id},
                            {"Name": "ESCALATION_LEVEL", "Value": str(escalation_level)}
                        ]
                    }]
                }
            },
            
            # Retry policy
            "RetryPolicy": {
                "MaximumRetryAttempts": 2,
                "MaximumEventAgeInSeconds": 3600
            },
            
            # Dead letter queue for permanent failures
            "DeadLetterConfig": {
                "Arn": settings.dlq_arn
            }
        },
        
        FlexibleTimeWindow={"Mode": "OFF"}
    )
```

### Cycle Worker Implementation

```python
# src/workers/cycle_worker.py

import os
import sys
from src.services.cycle_service import execute_escalation
from src.core.logging import setup_logging

def main():
    """Entry point for cycle worker container."""
    
    # Get environment variables
    cycle_id = os.environ.get("CYCLE_ID")
    escalation_level = int(os.environ.get("ESCALATION_LEVEL", "1"))
    
    if not cycle_id:
        print("ERROR: CYCLE_ID environment variable required", file=sys.stderr)
        sys.exit(1)
    
    # Setup logging (CloudWatch)
    logger = setup_logging(
        service="cycle-worker",
        cycle_id=cycle_id,
        escalation_level=escalation_level
    )
    
    logger.info(f"Cycle worker starting: cycle={cycle_id}, escalation={escalation_level}")

    try:
        # Execute escalation (isolated execution)
        execute_escalation(cycle_id, escalation_level)

        logger.info(f"Cycle worker completed successfully")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Cycle worker failed: {e}", exc_info=True)
        sys.exit(1)  # Non-zero exit = failure (triggers retry if configured)

if __name__ == "__main__":
    main()
```

### Error Handling and Isolation

```python
# src/services/cycle_service.py

def execute_escalation(cycle_id: str, escalation_level: int):
    """Execute escalation in isolated container.
    
    Errors in this function only affect THIS cycle/escalation.
    Other cycles/campaigns continue normally.
    """
    
    try:
        # 1. Load cycle and campaign
        cycle = get_cycle(cycle_id)
        campaign = get_campaign(cycle.campaign_id)
        
    except RecordNotFound as e:
        logger.error(f"Cycle or campaign not found: {e}")
        raise  # Fatal error, don't retry
    
    try:
        # 2. Query data source (ISOLATED - failure doesn't affect other campaigns)
        all_records = fetch_from_data_source(campaign.data_source)
        
    except DataSourceError as e:
        # Bad data source only affects THIS campaign
        logger.error(f"Data source error for campaign {campaign.id}: {e}")
        notify_campaign_owner(campaign.owner_email, error=e)
        raise  # Will trigger retry
    
    try:
        # 3. Apply mode filter
        filtered_records = apply_mode_filter(all_records, campaign.mode, campaign.mode_config)
        
        # 4. Check verification status
        unverified_records = [r for r in filtered_records if not is_verified(r, cycle.start_date)]
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise
    
    try:
        # 5. Send notifications (ISOLATED - template errors don't affect other campaigns)
        for contact, records in group_by_contact(unverified_records):
            send_notification(contact, records, campaign)
            
    except TemplateError as e:
        # Template error only affects THIS campaign
        logger.error(f"Template error for campaign {campaign.id}: {e}")
        notify_campaign_owner(campaign.owner_email, error=e)
        raise  # Will trigger retry
    
    # 6. Update cycle stats
    update_cycle_stats(cycle_id, len(unverified_records))
    
    logger.info(f"Escalation complete: {len(unverified_records)} notifications sent")
```

## AWS Infrastructure (Terraform/CloudFormation)

### ECS Cluster and Task Definitions

```hcl
# ECS Cluster
resource "aws_ecs_cluster" "echo" {
  name = "echo-cluster"
}

# API Service (Long-Running)
resource "aws_ecs_service" "echo_api" {
  name            = "echo-api"
  cluster         = aws_ecs_cluster.echo.id
  task_definition = aws_ecs_task_definition.echo_api.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets         = var.private_subnets
    security_groups = [aws_security_group.echo_api.id]
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.echo_api.arn
    container_name   = "echo-api"
    container_port   = 8000
  }
}

# Cycle Worker Task Definition (On-Demand)
resource "aws_ecs_task_definition" "echo_cycle_worker" {
  family                   = "echo-cycle-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn
  
  container_definitions = jsonencode([{
    name  = "echo-worker"
    image = "${var.ecr_repository}/echo-worker:latest"
    
    environment = [
      {name = "DATABASE_URL", value = var.database_url},
      {name = "AWS_REGION", value = var.aws_region}
    ]
    
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/echo-cycle-worker"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "worker"
      }
    }
  }])
}

# EventBridge IAM Role (can launch ECS tasks)
resource "aws_iam_role" "eventbridge_ecs" {
  name = "echo-eventbridge-ecs-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge_ecs" {
  role = aws_iam_role.eventbridge_ecs.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ecs:RunTask"
      ]
      Resource = aws_ecs_task_definition.echo_cycle_worker.arn
    }]
  })
}
```

## Platform Campaign (Dogfooding)

### Concept: ECHO Managing ECHO

**Purpose:** Use ECHO to verify ECHO's own campaigns are properly maintained.

**The Platform Campaign** is a special campaign managed by ECHO administrators that monitors all other campaigns in the system. This serves multiple purposes:
- **Dogfooding** - ECHO uses ECHO (validates the product works)
- **Campaign health monitoring** - Ensures campaigns are actively maintained
- **Ownership validation** - Verifies campaign owners are current employees
- **Demonstration** - Shows ECHO in action to stakeholders

### Implementation

**Data Source:**
```python
{
  "data_source": {
    "type": "postgresql",
    "connection_string": "${DATABASE_URL}",  # Same database ECHO uses
    "query": """
      SELECT
        id::text as object_id,
        name,
        owner_email as primary_owner,
        created_by as secondary_owner,
        last_run_at,
        enabled,
        created_at
      FROM campaigns
      WHERE id != :platform_campaign_id  -- EXCLUDE SELF
      ORDER BY name
    """
  }
}
```

**Escalation Rules:**
```python
{
  "escalation_rules": [
    {
      "level": 0,
      "delay_days": 0,
      "recipients": ["primary_owner"]  # Campaign owner (initial notification)
    },
    {
      "level": 1,
      "delay_days": 14,
      "recipients": ["primary_owner", "secondary_owner"]  # Notify both owners
    },
    {
      "level": 2,
      "delay_days": 30,
      "recipients": ["primary_owner", "primary_owner.manager", "echo-admins@company.com"]
    }
  ]
}
```

**Verification Detection:**
```python
# A campaign is "verified" if it has run recently
def is_verified(campaign_record, cycle_start_date):
    """Campaign is verified if it ran in the last 90 days."""

    if not campaign_record.last_run_at:
        return False  # Never run

    days_since_run = (cycle_start_date - campaign_record.last_run_at).days
    return days_since_run <= 90  # Stale after 90 days
```

### Platform Campaign Configuration Example

```python
{
  "name": "Platform Campaign - ECHO Campaign Health",
  "description": "Monitors all ECHO campaigns to ensure they are actively maintained",

  "data_source_type": "sql",
  "data_source_config": {
    "connection_string": "postgresql://...",
    "query": "SELECT ... FROM campaigns WHERE id != :platform_campaign_id"
  },

  "campaign_schedule": "cron(0 0 1 * ? *)",  # Monthly

  "escalation_rules": [
    {"level": 0, "delay_days": 0, "recipients": ["primary_owner"]},
    {"level": 1, "delay_days": 14, "recipients": ["primary_owner", "secondary_owner"]},
    {"level": 2, "delay_days": 30, "recipients": ["primary_owner", "primary_owner.manager", "echo-admins@company.com"]}
  ],

  "notification_template": {
    "email": {
      "subject": "ECHO Platform: Your campaign needs attention",
      "body_html": """
        <h1>Hi {{ recipient.name }},</h1>
        <p>Your ECHO campaign needs attention:</p>
        <ul>
        {% for record in records %}
          <li>
            <strong>{{ record.source_data.name }}</strong><br>
            Last run: {{ record.source_data.last_run_at or 'Never' }}<br>
            Status: {{ 'Enabled' if record.source_data.enabled else 'Disabled' }}
          </li>
        {% endfor %}
        </ul>
        <p>Please review and update your campaign configuration.</p>
      """
    }
  },

  "mode": "all_items",
  "owner_email": "echo-admins@company.com",
  "created_by": "echo-admin"
}
```

### Key Features

**Self-Exclusion:**
- Platform Campaign's data source query excludes itself (`WHERE id != :platform_campaign_id`)
- Prevents infinite recursion
- Ensures only actual user campaigns are monitored

**Modifiable Like Any Campaign:**
- Platform Campaign is stored in the `campaigns` table like any other
- Users with `echo.admin` role can edit it through the API/UI
- No special code or hardcoded logic
- Can be disabled, modified, or deleted if needed
- Owner: `echo-admins@company.com` (mapped to Entra group)

**Benefits:**
- Validates ECHO works as designed
- Ensures campaigns stay active and maintained
- Demonstrates manager escalation in production
- Provides confidence in the system

### Setup

1. Create Platform Campaign via API (after ECHO is deployed)
2. Store campaign_id as environment variable or config
3. Data source query uses campaign_id to exclude self
4. ECHO admins receive notifications about stale campaigns
5. Platform Campaign becomes a living example of ECHO in action

## Verification Strategy

### ECHO's Verification Approach

**Design Principle:** ECHO orchestrates notifications but doesn't manage source data.

**Notification URLs** point users to where they can review/update records:
- **Source has UI:** Link to source system (service catalog, CMDB, etc.)
- **Source has no UI:** Link to ECHO's simple verification page (read-only)
- **Team has custom portal:** Link to team's verification portal

### What's Included in ECHO

**1. Verification Tracking API**

ECHO provides an API for tracking verifications (regardless of where they happen):

```python
# POST /api/cycles/{cycle_id}/records/{record_id}/verify
{
  "verified_by": "alice@company.com",
  "comment": "Reviewed and confirmed current",
  "verification_source": "manual"  # or "source_system", "portal", etc.
}

# Response
{
  "id": "verification-uuid",
  "cycle_id": "cycle-123",
  "record_id": "service-456",
  "verified_by": "alice@company.com",
  "verified_at": "2024-01-15T10:30:00Z",
  "verification_type": "confirmed"
}
```

**2. Simple Read-Only Verification Page**

ECHO includes a minimal verification page for cases where no editing is needed:

```
URL: https://echo.company.com/verify/{cycle_id}/{record_id}

Shows:
┌─────────────────────────────────────────────┐
│ Verify: Payment Processing API              │
├─────────────────────────────────────────────┤
│ Resource Details (read-only):               │
│   Name: Payment Processing API              │
│   Owner: Alice Smith                        │
│   Tech Lead: Bob Jones                      │
│   Last Updated: 2024-01-15                  │
│                                             │
│ ⚠️ To update this data, contact:            │
│    data-team@company.com                    │
│                                             │
│ Verification Actions:                       │
│   ✅ Mark as Verified                       │
│   💬 Add Comment: [text field]              │
│                                             │
│ [Verify] [Add Comment]                      │
└─────────────────────────────────────────────┘
```

**3. Configurable Notification URLs**

Campaign owners specify which templates to use for each channel:

```python
{
  "name": "Service Verification",

  "notification_templates": {
    "email": "service_verification_email",
    "teams": "service_verification_teams"
  }
}
```

URLs are embedded directly in the template content:

```html
<!-- Email template: service_verification_email -->
<a href="https://service-catalog.company.com/services/{{ record.object_id }}">Verify</a>

<!-- OR point to ECHO's simple page -->
<a href="https://echo.company.com/verify/{{ cycle.id }}/{{ record.id }}">Verify</a>

<!-- OR point to custom verification portal -->
<a href="https://service-portal.company.com/verify?id={{ record.object_id }}&cycle={{ cycle.id }}">Verify</a>
```

### Database Schema

```sql
-- Verification tracking
CREATE TABLE verifications (
  id UUID PRIMARY KEY,
  cycle_id UUID REFERENCES cycles(id),
  record_id VARCHAR(255) NOT NULL,  -- object_id from source

  -- Who and when
  verified_by VARCHAR(255) NOT NULL,
  verified_at TIMESTAMP NOT NULL,

  -- Verification details
  verification_type VARCHAR(50) NOT NULL,  -- 'confirmed', 'comment', 'source_updated'
  verification_source VARCHAR(50),          -- 'manual', 'portal', 'source_system'
  comment TEXT,

  -- Audit
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_verifications_cycle ON verifications(cycle_id);
CREATE INDEX idx_verifications_record ON verifications(record_id);
CREATE INDEX idx_verifications_verified_at ON verifications(verified_at);
```

### Verification Detection (Updated)

```python
def is_verified(record, cycle_start_date):
    """Check if record was verified since cycle started.

    Checks multiple sources (in order):
    1. Explicit verification in ECHO
    2. Timestamp in source data (last_verified, last_updated)
    3. Hash change detection
    """

    # Tier 1: Explicit verification via ECHO API
    verification = get_verification(
        record_id=record.object_id,
        since=cycle_start_date
    )
    if verification:
        return True

    # Tier 2: Timestamp in source data
    if record.source_data.get("last_verified"):
        last_verified = parse_datetime(record.source_data["last_verified"])
        if last_verified >= cycle_start_date:
            return True

    if record.source_data.get("last_updated"):
        last_updated = parse_datetime(record.source_data["last_updated"])
        if last_updated >= cycle_start_date:
            return True

    # Tier 3: Hash change (any field changed = verified)
    if record_hash_changed(record, cycle_start_date):
        return True

    return False
```

### API Endpoints

```python
# Verify a record
@app.post("/api/cycles/{cycle_id}/records/{record_id}/verify")
async def verify_record(
    cycle_id: str,
    record_id: str,
    verification: VerificationCreate,
    user = Depends(get_current_user)
):
    """Mark record as verified."""

    result = await verification_service.create_verification(
        cycle_id=cycle_id,
        record_id=record_id,
        verified_by=user["email"],
        verification_type=verification.type,
        verification_source=verification.source,
        comment=verification.comment
    )

    return result

# Get verification page (simple UI)
@app.get("/verify/{cycle_id}/{record_id}")
async def verification_page(cycle_id: str, record_id: str):
    """Show simple verification page."""

    cycle = await get_cycle(cycle_id)
    campaign = await get_campaign(cycle.campaign_id)

    # Fetch record from data source
    data_source = create_data_source(campaign.data_source)
    record = await data_source.get_record(record_id)

    return templates.TemplateResponse("verification/simple.html", {
        "cycle": cycle,
        "campaign": campaign,
        "record": record
    })
```

## ECHO Verification Portal Kit (Separate Product)

**Note:** For data sources that don't have a UI and need editing capabilities, we provide a separate optional product.

### Concept

The **ECHO Verification Portal Kit** is a standalone template/boilerplate that teams can deploy if their data source needs a verification UI.

**Separation of Concerns:**
- **ECHO:** Campaign orchestration, notifications, verification tracking
- **Verification Portal:** Data viewing/editing, user interface

### Architecture

```
┌──────────────────────────────────────────────────────┐
│  ECHO (Core Product)                                 │
│  - Manages campaigns                                 │
│  - Sends notifications                               │
│  - Provides verification tracking API                │
│  - Simple read-only verification page                │
└──────────────────────────────────────────────────────┘
                    ↑
                    | Calls verification API
                    |
┌──────────────────────────────────────────────────────┐
│  ECHO Verification Portal Kit (Optional)             │
│  - Separate deployment (team-owned)                  │
│  - Reads from data source                            │
│  - Provides edit forms                               │
│  - Writes back to data source                        │
│  - Calls ECHO verification API                       │
└──────────────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────┐
│  Data Source (SQL, API, etc.)                        │
│  - Source of truth for data                          │
└──────────────────────────────────────────────────────┘
```

### When Teams Need It

**Use Verification Portal Kit if:**
- ✅ Data source has no UI (SQL view, API endpoint, CSV)
- ✅ Users need to edit data to complete verification
- ✅ Team wants a lightweight, purpose-built verification interface

**Don't need it if:**
- ❌ Source system has its own UI (just link to it)
- ❌ Data is read-only (use ECHO's simple verification page)
- ❌ Team wants to build their own custom UI

### How It Works

**1. Team deploys verification portal:**
```bash
# Clone template
git clone https://github.com/company/echo-verification-portal-kit
cd echo-verification-portal-kit

# Configure for their data source
cp config.example.yaml config.yaml
# Edit config.yaml with data source details

# Deploy
docker compose up
```

**2. Configure ECHO campaign and template:**

Campaign configuration:
```python
{
  "name": "Service Verification",
  "notification_templates": {
    "email": "service_portal_verification_email"
  }
}
```

Email template content:
```html
<a href="https://service-portal.company.com/verify?id={{ record.object_id }}&cycle={{ cycle.id }}">Verify in Portal</a>
```

**3. User workflow:**
```
User receives notification
  ↓ Clicks link
Portal loads record from data source
  ↓ Shows edit form
User updates fields
  ↓ Saves
Portal writes to data source
  ↓ Calls ECHO verification API
ECHO marks record as verified
  ↓
Next escalation skips this record ✅
```

### Portal Configuration Example

```yaml
# config.yaml (team customizes for their source)
portal:
  name: "Service Registry Verification Portal"
  base_url: "https://service-portal.company.com"

data_source:
  type: "sql"
  connection_string: "${DATABASE_URL}"
  table: "services"
  primary_key: "service_id"

  editable_fields:
    - name: "owner_email"
      type: "email"
      required: true
      validation: "^[a-z.]+@company\\.com$"

    - name: "tech_lead"
      type: "string"
      required: true

    - name: "description"
      type: "textarea"
      required: false

echo_integration:
  api_url: "https://echo.company.com/api"
  auth:
    type: "azure_ad"
    client_id: "${AZURE_CLIENT_ID}"
    client_secret: "${AZURE_CLIENT_SECRET}"
```

### Portal Features

**MVP Portal Provides:**
- ✅ Generic data display (read from source)
- ✅ Edit forms (write to source)
- ✅ Field validation
- ✅ ECHO verification API integration
- ✅ Azure AD authentication
- ✅ Audit trail of changes

**Teams Can Customize:**
- UI/UX (templates, styling)
- Field types and validation
- Additional features (comments, attachments, approvals)
- Integration with other systems

### Benefits of Separation

**For ECHO:**
- ✅ Focused scope (orchestration, not data management)
- ✅ Simpler codebase
- ✅ No need to handle every data source type
- ✅ Easier to maintain

**For Teams:**
- ✅ Optional (only deploy if needed)
- ✅ Customizable (fork and modify)
- ✅ Independent deployment (doesn't affect ECHO)
- ✅ Team-owned (manage their own infrastructure)

**For the Product:**
- ✅ Cleaner architecture
- ✅ Reusable template
- ✅ Community can contribute portal variations
- ✅ Different portals for different use cases

### Documentation

**For teams needing a verification UI:**

See: **[ECHO Verification Portal Kit](https://github.com/company/echo-verification-portal-kit)** (separate repository)

**Quick Start:**
1. Clone the template
2. Configure for your data source
3. Deploy the portal
4. Point your ECHO campaign's `verification_url_template` to the portal
5. Users edit data in the portal, which calls ECHO's verification API

