# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ECHO is an enterprise campaign management system for automated resource inventory verification. It orchestrates periodic notification campaigns to maintain data accuracy without modifying source systems. The system uses AWS EventBridge Scheduler to trigger campaigns, SQS queues to process events, and maintains campaign metadata in a local database.

**Key principle**: ECHO has read-only access to external data sources. It never modifies source data - only reads and sends notifications.

## Development Commands

### Running the Application

```bash
# Development server with auto-reload (recommended for development)
uv run fastapi dev src/main.py

# Production server
uv run fastapi run src/main.py

# Standalone scheduler mode (no web API, only background processing)
uv run python src/main.py
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_campaigns.py

# Run with coverage
uv run pytest --cov=src

# Run single test
uv run pytest tests/test_api.py::test_read_main
```

### Dependencies

```bash
# Install all dependencies (including dev dependencies)
uv sync

# Install only production dependencies
uv sync --only-group main

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --group dev package-name
```

### Code Quality

```bash
# Format imports
uv run isort src/

# Lint with pylint
uv run pylint src/

# Type check with pyright
pyright
```

## Architecture

### Layer Structure

```
┌─────────────────────────────────────┐
│  API Layer (api/routes/)            │  ← FastAPI routes, HTTP handling
├─────────────────────────────────────┤
│  Service Layer (services/)          │  ← Business logic orchestration
├─────────────────────────────────────┤
│  Core Layer (core/)                 │  ← Domain models, AWS clients
├─────────────────────────────────────┤
│  Database Layer (db/)               │  ← SQLAlchemy persistence
└─────────────────────────────────────┘
```

### Campaign Execution Flow

1. **Campaign Creation**: User creates a campaign via API → Campaign saved to DB → AWS EventBridge schedule group created → Main campaign schedule created
2. **Campaign Trigger**: EventBridge fires campaign schedule → Message sent to Queue 1 (QUEUE_1_URL)
3. **Cycle Schedule Creation**: Queue 1 handler processes message → Creates N one-time cycle schedules (where N = campaign.max_events) based on campaign.cycle_schedule cron expression
4. **Cycle Execution**: Each cycle schedule fires → Message sent to Queue 2 (QUEUE_2_URL) → Queue 2 handler executes campaign cycle logic (TBD: notification sending, data fetching)

### Dual Scheduling System

ECHO uses two schedulers working together:

1. **AWS EventBridge Scheduler** (`core/scheduler.py`):
   - Manages production-grade scheduled triggers
   - Creates schedule groups per campaign: `campaign_{id}_group`
   - Main campaign schedule: `campaign_{id}_schedule` (recurring)
   - Cycle schedules: `campaign_{id}_cycle_{n}_schedule` (one-time, auto-deleted after execution)
   - Uses AWS cron format: `cron(minutes hours day month weekday year)` or one-time: `at(YYYY-MM-DDTHH:MM:SS)`

2. **SQS Queue Consumers** (`core/lifecycle.py`, `core/queue_handlers.py`):
   - Started as background asyncio tasks during application lifespan
   - Queue 1: Receives campaign start triggers → Creates cycle schedules
   - Queue 2: Receives cycle execution triggers → Executes notification logic
   - Both queues polled continuously with max 5 messages per batch

### Data Flow Between Layers

- **Pydantic models** (`core/models.py`): Domain layer, used in API contracts and business logic
- **SQLAlchemy models** (`db/schemas.py`): Persistence layer, database schemas
- **Conversion**: Service layer uses `to_domain()` and `to_schema()` functions to translate between layers

### AWS Integration Details

- **Schedule Groups**: One per campaign, contains all schedules for that campaign
- **Schedule Naming**:
  - Main: `campaign_{id}_schedule`
  - Cycles: `campaign_{id}_cycle_{count}_schedule` (count starts at 1)
- **Target Configuration**: All schedules target SQS queues with JSON payloads containing campaign_id, timestamps, and cycle counts
- **Cleanup**: When deleting a campaign, the entire schedule group is deleted (cascades to all schedules)

## Important Conventions

### AWS Cron Format

ECHO uses **AWS cron expressions**, not standard Unix cron:
- Format: `cron(minutes hours day month weekday year)`
- Example: `cron(0 12 * * ? *)` = daily at noon UTC
- Note the `?` for day-of-month or day-of-week when using wildcards
- For one-time schedules: `at(YYYY-MM-DDTHH:MM:SS)` format

Use the `aws-croniter` library to work with these expressions, not standard `croniter`.

### Campaign Requirements

Every campaign must have:
- `campaign_schedule`: AWS cron expression for when to start the campaign
- `cycle_schedule`: AWS cron expression for how often cycle events occur
- `max_events`: Number of cycle events to create (determines how many one-time schedules)
- `conn_string`: Connection string to read-only data source

### Database Transactions

Critical pattern for campaign operations:
```python
with sessionmaker(bind=echo_engine)() as session:
    # 1. Perform DB operation
    session.add(campaign_model)
    session.flush()  # Get ID without committing

    # 2. Perform AWS operations
    try:
        await create_schedule_group(campaign)
        await create_campaign_schedule(campaign)
        session.commit()  # Only commit if AWS succeeds
    except Exception:
        session.rollback()  # Rollback if AWS fails
        raise
```

Always coordinate DB commits with AWS operations to maintain consistency.

### Type Hints

Use Python 3.10+ union syntax:
- ✅ `Campaign | None`
- ❌ `Optional[Campaign]`

### Import Organization

Three groups, alphabetically sorted within each:
1. Standard library
2. Third-party (FastAPI, SQLAlchemy, boto3, etc.)
3. Local (api, core, db, services, utils)

Configured via `isort` with `known_first_party = ["api", "core", "db", "services", "utils"]`

### API Routes

- **HTML/Template routes**: No `/api` prefix, in `api/routes/basic.py`
- **REST API routes**: `/api` prefix, in `api/routes/campaigns.py`
- Use async handlers (`async def`) for I/O operations
- Always use Pydantic models for request/response validation

## Configuration

`core/config.py` contains hardcoded AWS resource ARNs and URLs:
- `QUEUE_1_URL`, `QUEUE_1_ARN`: Campaign start trigger queue
- `QUEUE_2_URL`, `QUEUE_2_ARN`: Cycle execution queue
- `EXECUTION_ROLE_ARN`: IAM role for EventBridge Scheduler to invoke SQS

**TODO**: These should be externalized to environment variables for multi-environment support.

## Testing

Test fixtures in `tests/conftest.py`:
- `client`: FastAPI TestClient for API testing
- `sample_campaign_data`: Valid campaign data dictionary

Tests must run from repository root with `uv run pytest` to ensure proper path resolution.

## Common Pitfalls

❌ **Don't** use standard cron format - use AWS cron format with `?` for wildcards
❌ **Don't** commit database transactions before AWS scheduler operations succeed
❌ **Don't** modify external data sources - ECHO is read-only
❌ **Don't** forget to create schedule groups before creating schedules
❌ **Don't** forget to clean up AWS schedules when deleting campaigns
❌ **Don't** use blocking I/O in async handlers - use `asyncio.to_thread()` for sync AWS SDK calls
❌ **Don't** skip the `session.flush()` before creating AWS schedules - you need the campaign ID first

## Documentation

- `README.md`: User-facing setup and usage guide
- `docs/Design.md`: System architecture and design principles
- `docs/basic_concepts.md`: Core concepts and terminology
- `docs/modes.md`: Different operational modes
- `docs/shared_responsibility_model.md`: Team responsibilities
- `docs/project_structure.md`: Detailed layer architecture
- `.github/copilot-instructions.md`: Additional development guidelines
