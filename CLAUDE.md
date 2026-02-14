# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

**ECHO is currently in the design phase.** No implementation code exists yet. The repository contains comprehensive design documentation.

## Your Role During Design Phase

When working on this project, you should:

1. **Help review and refine design documents** in the `docs/` directory
2. **Identify gaps or inconsistencies** in the design
3. **Answer questions about feasibility** and technical approaches
4. **Suggest improvements** to architecture or workflows
5. **Help resolve open questions** documented in `docs/06-open-questions.md`

## Documentation Structure

Read these documents in order to understand the project:

1. `docs/00-overview.md` - Project overview and value proposition
2. `docs/01-core-concepts.md` - Core terminology and entities
3. `docs/02-architecture.md` - System architecture and components
4. `docs/03-data-model.md` - Data structures and schemas
5. `docs/04-workflows.md` - Operational workflows
6. `docs/06-open-questions.md` - Unresolved design decisions
7. `docs/implementation-plan.md` - Tech stack and development plan

Archived documentation (previous iterations) is in `docs/archive/`.

## Core Principles

When suggesting changes or answering questions, always consider these principles:

1. **Read-Only Data Access**: ECHO never modifies external data sources
2. **Data Ownership**: Teams control their own source systems
3. **Minimal Integration**: Lowest possible burden on integrating teams
4. **Extensibility**: Pluggable components for data sources and notification channels
5. **Simplicity**: Easy to configure and operate

## Key Design Constraints

- Data sources must provide: `object_id` and at least one contact field
- Campaigns must have: campaign schedule, cycle schedule, escalation rules
- Campaign frequency must be > cycle duration (avoid overlap)
- All external data access is read-only (strict requirement)
- AWS cron format required (not standard cron)

## Code Standards (For Future Implementation)

When implementation begins, follow these standards:

### Python Style
- **PEP 8** compliant (enforced by ruff)
- **PEP 484** type hints required for all functions
- **PEP 257** Google-style docstrings for public APIs
- Line length: 88 characters
- Python 3.13+ syntax (use `str | None` not `Optional[str]`)

### Naming Conventions
- Files: `snake_case.py`
- Functions/Variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

### Code Quality
- Linting: `ruff` (replaces flake8, black, isort)
- Type checking: `mypy --strict`
- Testing: `pytest` with `pytest-asyncio`
- Pre-commit hooks enforce all checks

### Project Structure
```
src/
├── api/          # FastAPI routes and HTTP handling
├── services/     # Business logic layer
├── core/         # Domain models (Pydantic)
├── db/           # Database models (SQLAlchemy)
├── integrations/ # External systems (data sources, notifications, schedulers)
├── templates/    # Jinja2 templates
└── utils/        # Utility functions
```

## Common Tasks (When Implementation Starts)

```bash
# Development
make dev          # Run development server
make test         # Run test suite
make lint         # Check code quality
make format       # Format code

# Database
make db-setup     # Initialize database
make db-migrate   # Run migrations
make db-seed      # Seed example data
```

## Design Review Questions to Consider

When reviewing the design, ask:

1. **Is this achievable?** Can the proposed solution be built with reasonable effort?
2. **Is this scalable?** Will it handle 100+ campaigns with 10,000+ records each?
3. **Is this maintainable?** Is the architecture clear and well-separated?
4. **Are there edge cases?** What happens when things go wrong?
5. **Is this user-friendly?** Is configuration intuitive for campaign owners?
6. **Are open questions resolved?** See `docs/06-open-questions.md`

## Helping with Open Questions

When addressing open questions in `docs/06-open-questions.md`:

1. **Understand the context** - Read related design docs
2. **Consider trade-offs** - What are pros/cons of each option?
3. **Think about MVP** - What's essential vs. nice-to-have?
4. **Validate assumptions** - Are the assumptions in the design correct?
5. **Document the decision** - Use the decision template in the open questions doc

## Important Context

- **Shared Responsibility Model**: ECHO provides notification orchestration; teams own their data
- **Multi-Tenancy**: Multiple teams use one ECHO instance (future requirement)
- **Campaign Modes**: Originally planned SVT/AVT/CVT modes may simplify to one flexible model
- **Verification Detection**: Critical decision - how to know when a resource is verified?
- **Scheduler Choice**: APScheduler (simple) vs. EventBridge (scalable) - likely use both

## When Implementation Begins

This file will be updated with:
- Specific development commands
- Architecture layer responsibilities
- Critical implementation patterns
- Common pitfalls to avoid
- Testing strategies

For now, focus on design review and helping make informed architectural decisions.
