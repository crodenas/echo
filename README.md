# ECHO - Enterprise Campaign Handling and Orchestration

**Status:** ✅ Simplified MVP - Ready for Implementation (8-10 weeks)

ECHO is an enterprise software system designed to help teams manage and verify resource inventory data through automated notification campaigns. The system enables teams to maintain data accuracy by sending periodic verification requests to resource contacts without requiring changes to existing data sources.

## What Problem Does ECHO Solve?

Enterprise teams struggle to keep resource inventory data (services, databases, servers, etc.) accurate and up-to-date:
- **Data goes stale** - Contact information becomes outdated over time
- **Manual verification is inconsistent** - Teams lack systematic verification processes
- **Redundant systems** - Multiple teams build their own notification infrastructure
- **Integration is invasive** - Existing solutions require schema changes to source systems

## The ECHO Solution

**Notification-as-a-Service** for enterprise resource verification:

- ✅ **Read-only integration** - No changes to your existing data sources
- ✅ **Automated campaigns** - Set schedules, define escalation policies, let it run
- ✅ **Manager escalations** - Automatically escalate to managers using `.manager` syntax
- ✅ **Employee directory integration** - Resolve SystemIds to emails, traverse hierarchy
- ✅ **Timestamp-based verification** - Simple, reliable verification detection

**MVP Scope:**
- PostgreSQL data sources (MySQL, REST API in MVP+)
- Email notifications (Teams, Slack in MVP+)
- Single tenant (multi-tenancy in MVP+)

## Key Features (MVP)

- **Campaign Management**: Create, schedule, and manage campaigns via REST API
- **Automated Scheduling**: AWS EventBridge for reliable cycle triggers
- **Manager Escalation Chains**: Support `owner.manager.manager` syntax
- **Employee Directory**: Azure AD protected API for contact resolution
- **Email Notifications**: AWS SES with Jinja2 templates
- **Contact Grouping**: One email per recipient with all their records
- **Timestamp Verification**: Require `last_verified` field in data source
- **Progress Tracking**: Monitor cycles and notification delivery

## Documentation

This repository contains comprehensive design documentation. Review in this order:

1. **[Overview](docs/00-overview.md)** - What ECHO is and why it exists
2. **[Core Concepts](docs/01-core-concepts.md)** - Campaigns, cycles, records, contacts
3. **[Architecture](docs/02-architecture.md)** - System components and data flow
4. **[Data Model](docs/03-data-model.md)** - Data sources, schemas, requirements
5. **[Workflows](docs/04-workflows.md)** - How campaigns execute end-to-end
6. **[Decisions](docs/decisions.md)** - ✅ **All design decisions (updated 2026-02-15 with MVP simplifications)**
7. **[Roadmap](docs/roadmap.md)** - ✅ **Feature roadmap by version (MVP, MVP+, Future)**
8. **[Implementation Plan](docs/implementation-plan.md)** - ✅ **Simplified MVP implementation plan (8-10 weeks)**

## Project Status

**Current Phase:** ✅ Simplified MVP Design → Ready for Implementation

- ✅ Core concepts defined
- ✅ Architecture designed (simplified for MVP)
- ✅ Data model specified
- ✅ Workflows documented
- ✅ **All design decisions finalized and simplified (2026-02-15)**
- ✅ **MVP scope reduced by ~30-40% (8-10 weeks vs 12-14 weeks)**
- ✅ **Roadmap created** - See [Roadmap](docs/roadmap.md)
- ⏳ Implementation Phase 1 ready to begin

**Key Simplifications:**
- Require `last_verified` timestamp (no hash-based verification)
- Email only (no Teams/Slack for MVP)
- PostgreSQL only (no multiple data sources)
- Background jobs (no per-escalation containers)
- Keep Employee Directory + `.manager` syntax ✅

**Next Steps:**
1. ~~Review and finalize design decisions~~ ✅ Complete
2. ~~Simplify MVP scope~~ ✅ Complete
3. **BEGIN Phase 1: Foundation implementation** (Week 1-2)

## Quick Start (When Implemented)

```bash
# Install dependencies
uv sync

# Setup database
make db-setup
make db-migrate

# Run development server
make dev

# Run tests
make test
```

See [Implementation Plan](docs/implementation-plan.md) for detailed setup instructions.

## Technology Stack (MVP)

- **Backend**: FastAPI + Python 3.13+ (async)
- **Database**: PostgreSQL + SQLAlchemy 2.0 (async)
- **Scheduling**: AWS EventBridge Scheduler (all environments)
- **Notifications**: AWS SES (email only for MVP)
- **Authentication**: Azure AD OAuth2
- **Employee Directory**: Azure AD protected REST API
- **Templates**: Jinja2 (file-based)
- **Deployment**: Single ECS service (API + background jobs)
- **Package Manager**: uv
- **Code Quality**: ruff, mypy, pytest

**Post-MVP:** Teams/Slack channels, MySQL/REST API sources, per-escalation containers

## Examples

See `examples/data/` for sample data structures:
- `Employees.json` - Employee data format
- `Reviewables1.json` - Example resource inventory
- `Reviewables2.json` - Additional resource examples

## Contributing

This project is currently in design phase. Feedback on design documents is welcome.

## Design Principles

1. **Read-Only Integration** - Never modify external data sources
2. **Data Ownership** - Teams retain full control of their systems
3. **Minimal Impact** - Lowest possible integration burden
4. **Extensibility** - Pluggable connectors for data sources and channels
5. **Simplicity** - Easy to configure, minimal maintenance

## License

[To be determined]

## Contact

[To be determined]
