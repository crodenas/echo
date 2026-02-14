# ECHO Documentation

This directory contains the complete design documentation for ECHO (Enterprise Campaign Handling and Orchestration).

## Documentation Status

**Current Phase:** Design and Planning
**Last Updated:** February 2026
**Implementation Status:** Not started

---

## Documentation Guide

Read these documents in order for complete understanding:

### 1. Core Design Documents

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [00-overview.md](00-overview.md) | What ECHO is, problems it solves, value proposition | 5 min |
| [01-core-concepts.md](01-core-concepts.md) | Fundamental concepts: campaigns, cycles, records, contacts | 10 min |
| [02-architecture.md](02-architecture.md) | System architecture, components, data flow, technology stack | 15 min |
| [03-data-model.md](03-data-model.md) | Data structures, schemas, database design, requirements | 15 min |
| [04-workflows.md](04-workflows.md) | End-to-end workflows, lifecycle management, edge cases | 15 min |

### 2. Decision & Planning Documents

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [05-feasibility-analysis.md](05-feasibility-analysis.md) | Feasibility assessment, risk analysis, effort estimates | 10 min |
| [06-open-questions.md](06-open-questions.md) | Unresolved design decisions requiring input | 15 min |
| [implementation-plan.md](implementation-plan.md) | Tech stack, project structure, development roadmap | 15 min |

### 3. Archive

| Location | Contents |
|----------|----------|
| [archive/](archive/) | Previous documentation iterations and superseded files |

---

## Quick Reference

### Design Principles

1. **Read-Only Integration** - Never modify external data sources
2. **Data Ownership** - Teams retain full control of their systems
3. **Minimal Impact** - Lowest possible integration burden
4. **Extensibility** - Pluggable components
5. **Simplicity** - Easy to configure and operate

### Key Constraints

- Data sources must provide: `object_id` and at least one contact
- Campaign frequency must exceed cycle duration
- All external data access is read-only (strict)
- AWS cron format required for schedules

### Technology Stack (Proposed)

- **Backend:** FastAPI + Python 3.13+
- **Database:** PostgreSQL + SQLAlchemy
- **Scheduling:** APScheduler (dev) / AWS EventBridge (prod)
- **Notifications:** AWS SES, Microsoft Teams, Slack
- **Code Quality:** ruff, mypy, pytest

---

## Open Questions Status

Critical questions requiring decisions before implementation:

- [ ] **Verification detection method** - How to determine if a record is verified?
- [ ] **Contact-less records** - How to handle records without contacts?
- [ ] **Cycle overlap** - How to prevent/handle overlapping cycles?
- [ ] **Notification channels** - Single vs. multiple channel strategy?
- [ ] **Scheduler choice** - APScheduler vs. EventBridge for production?

See [06-open-questions.md](06-open-questions.md) for details and options.

---

## Document Changelog

### 2026-02-13 - Documentation Reorganization
- Restructured into numbered, sequential documents
- Consolidated overlapping content from multiple sources
- Created feasibility analysis
- Identified and documented open questions
- Archived outdated documentation

### Previous Iterations
- See `archive/` directory for historical documentation

---

## How to Contribute

### Reviewing Design

1. Read documents in sequence (00 → 06)
2. Note any gaps, inconsistencies, or concerns
3. Review open questions and provide input
4. Suggest improvements to architecture or workflows

### Making Decisions

For open questions:
1. Review options and trade-offs in [06-open-questions.md](06-open-questions.md)
2. Consider MVP vs. future features
3. Document decision using provided template
4. Update related design documents

### Updating Documentation

When making changes:
1. Keep documents in sync (cross-reference updates)
2. Update this README if structure changes
3. Note significant changes in changelog above
4. Move superseded content to `archive/`

---

## Next Steps

1. **Review all design documents** to understand the full system
2. **Resolve critical open questions** (marked with priority in 06-open-questions.md)
3. **Validate feasibility** using the analysis in 05-feasibility-analysis.md
4. **Finalize MVP scope** based on effort estimates
5. **Begin implementation** following the plan in implementation-plan.md

---

## Questions or Feedback

- Design questions: Review [06-open-questions.md](06-open-questions.md)
- Architecture concerns: See [02-architecture.md](02-architecture.md)
- Feasibility doubts: Check [05-feasibility-analysis.md](05-feasibility-analysis.md)
- Implementation details: Consult [implementation-plan.md](implementation-plan.md)
