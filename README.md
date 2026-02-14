# ECHO - Enterprise Campaign Handling and Orchestration

**Status:** ✅ Design Complete - Ready for Implementation

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
- ✅ **Multi-tenant** - One system supports multiple teams and campaigns
- ✅ **Flexible data sources** - SQL databases, REST APIs, HTTP endpoints
- ✅ **Multi-channel notifications** - Email, Microsoft Teams, Slack

## Key Features

- **Campaign Management**: Create, schedule, and manage notification campaigns
- **Automated Scheduling**: Periodic verification cycles with configurable frequency
- **Escalation Policies**: Multi-level notification escalations with custom recipients
- **Template System**: Customizable notification templates per channel
- **Contact Grouping**: One notification per user with all their assigned resources
- **Progress Tracking**: Monitor verification status and campaign performance

## Documentation

This repository contains comprehensive design documentation. Review in this order:

1. **[Overview](docs/00-overview.md)** - What ECHO is and why it exists
2. **[Core Concepts](docs/01-core-concepts.md)** - Campaigns, cycles, records, contacts
3. **[Architecture](docs/02-architecture.md)** - System components and data flow
4. **[Data Model](docs/03-data-model.md)** - Data sources, schemas, requirements
5. **[Workflows](docs/04-workflows.md)** - How campaigns execute end-to-end
6. **[Decisions](docs/decisions.md)** - ✅ **All design decisions (finalized 2026-02-14)**
7. **[Feasibility Analysis](docs/05-feasibility-analysis.md)** - System is achievable in 12-14 weeks
8. **[Implementation Plan](docs/implementation-plan.md)** - Tech stack and roadmap

## Project Status

**Current Phase:** ✅ Design Complete → Ready for Implementation

- ✅ Core concepts defined
- ✅ Architecture designed
- ✅ Data model specified
- ✅ Workflows documented
- ✅ **All design decisions finalized (2026-02-14)**
- ✅ **Feasibility validated**
- ⏳ Implementation Phase 1 ready to begin

**Next Steps:**
1. ~~Review and finalize design decisions~~ ✅ Complete - See [Decisions](docs/decisions.md)
2. ~~Validate feasibility and scope~~ ✅ Complete - See [Feasibility Analysis](docs/05-feasibility-analysis.md)
3. **BEGIN Phase 1: Foundation implementation** (2-3 weeks)

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

## Technology Stack (Proposed)

- **Backend**: FastAPI + Python 3.13+
- **Database**: PostgreSQL + SQLAlchemy
- **Scheduling**: APScheduler (dev) / AWS EventBridge (prod)
- **Notifications**: AWS SES, Microsoft Teams, Slack
- **Templates**: Jinja2
- **Package Manager**: uv
- **Code Quality**: ruff, mypy, pytest

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
