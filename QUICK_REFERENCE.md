# Quick Reference - New Project Structure

## Directory Cheat Sheet

| Directory | Purpose | What Goes Here |
|-----------|---------|----------------|
| `src/api/routes/` | HTTP endpoints | FastAPI route handlers |
| `src/services/` | Business logic | Campaign operations, orchestration |
| `src/core/` | Domain layer | Pydantic models, config, utilities |
| `src/db/` | Data layer | SQLAlchemy schemas, engine config |
| `src/utils/` | Utilities | SQS consumer, queue watcher |
| `src/templates/` | UI | Jinja2 HTML templates |
| `tests/` | Testing | Pytest test files |
| `examples/` | Samples | Example data, configurations |
| `scripts/` | Tools | Utility scripts, migrations |
| `docs/` | Documentation | Architecture, design docs |

## Import Patterns

### Services (Business Logic)
```python
from services import campaign_service
result = await campaign_service.create_campaign(campaign)
```

### Models (Domain)
```python
from core.models import Campaign, CampaignCreate
campaign = Campaign(name="Test", ...)
```

### Database
```python
from db import echo_engine, CampaignSchema
from sqlalchemy.orm import sessionmaker
```

### Configuration
```python
from core import config
queue_url = config.QUEUE_1_URL
```

## Common Commands

```bash
# Development
uv run fastapi dev src/main.py          # Run dev server
uv sync                                  # Install dependencies

# Testing
uv run pytest                            # Run all tests
uv run pytest tests/test_api.py -v      # Run specific tests
uv run pytest -k "campaign"              # Run tests matching pattern

# Code Quality
uv run isort src/                        # Sort imports
uv run pylint src/                       # Lint code
```

## File Templates

### New Service (`src/services/my_service.py`)
```python
"""My service module.

Description of service responsibilities.
"""

from typing import List

from sqlalchemy.orm import sessionmaker

from core.models import MyModel
from db import echo_engine
from db.schemas import MySchema


async def my_operation(data: MyModel) -> MyModel:
    """Perform operation on data.

    Args:
        data: Input data model

    Returns:
        Result model
    """
    with sessionmaker(bind=echo_engine)() as session:
        # Implementation
        pass
```

### New Test (`tests/test_my_feature.py`)
```python
"""Tests for my feature."""

import pytest


class TestMyFeature:
    """Test suite for my feature."""

    def test_basic_case(self):
        """Test basic functionality."""
        assert True


@pytest.mark.asyncio
class TestMyFeatureAsync:
    """Async test suite."""

    async def test_async_case(self):
        """Test async functionality."""
        assert True
```

## Architecture Quick View

```
Request Flow:
────────────
Browser/API Client
    ↓
api/routes/*.py (HTTP handling)
    ↓
services/*.py (Business logic)
    ↓
├─→ db/schemas.py (Persistence)
└─→ core/scheduler.py (AWS EventBridge)
```

## Key Files

| File | Purpose |
|------|---------|
| `src/main.py` | Application entry point |
| `src/services/campaign_service.py` | Campaign CRUD + AWS coordination |
| `src/core/models.py` | Pydantic domain models |
| `src/core/scheduler.py` | AWS EventBridge client |
| `src/core/lifecycle.py` | App startup/shutdown, SQS consumers |
| `src/core/employees.py` | Employee data access |
| `src/utils/queue_watcher.py` | SQS consumer implementation |
| `src/db/schemas.py` | SQLAlchemy ORM models |
| `tests/conftest.py` | Pytest fixtures |
| `pyproject.toml` | Dependencies & config |

## Layer Responsibilities

**API Layer** - Request/Response, Validation
- No business logic
- HTTP status codes
- Pydantic validation

**Service Layer** - Business Operations
- Transaction management
- Service orchestration
- Error handling

**Core Layer** - Domain Models
- Data structures
- Business constants
- Utilities

**Database Layer** - Persistence
- Schema definitions
- Query execution
- Database config

## Documentation

- **Architecture**: [docs/project_structure.md](docs/project_structure.md)
- **Migration**: [docs/MIGRATION.md](docs/MIGRATION.md)
- **Summary**: [RESTRUCTURE_SUMMARY.md](RESTRUCTURE_SUMMARY.md)
- **API Docs**: http://localhost:8000/docs (when running)
