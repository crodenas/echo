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
| [decisions.md](decisions.md) | **✅ All design decisions (FINALIZED 2026-02-14)** | 25 min |
| [05-feasibility-analysis.md](05-feasibility-analysis.md) | Feasibility assessment, risk analysis, effort estimates | 10 min |
| [06-open-questions.md](06-open-questions.md) | ~~Unresolved~~ **RESOLVED** design decisions | 15 min |
| [implementation-plan.md](implementation-plan.md) | Tech stack, project structure, development roadmap | 20 min |
| [verification-portal-kit.md](verification-portal-kit.md) | **Separate optional product** for data sources without UIs | 15 min |

### 3. Archive

| Location | Contents |
|----------|----------|
| [archive/](archive/) | Previous documentation iterations and superseded files |

---

## Quick Reference

### Design Principles

1. **API-First** - All functionality via REST API, UI is optional
2. **Orchestration, Not Data Management** - ECHO sends notifications and tracks verifications, doesn't edit source data
3. **Separation of Concerns** - Verification UIs are separate optional products
4. **Data Ownership** - Teams retain full control of their systems
5. **Minimal Impact** - Lowest possible integration burden
6. **Extensibility** - Pluggable components (data sources, channels, templates)
7. **Simplicity** - Easy to configure and operate

### Key Constraints

- Data sources must provide: `object_id` and at least one contact
- Campaign frequency must exceed cycle duration
- All external data access is read-only (strict)
- AWS cron format required for schedules

### Technology Stack (Proposed)

- **Backend:** FastAPI + Python 3.13+
- **Database:** PostgreSQL + SQLAlchemy
- **Scheduling:** AWS EventBridge Scheduler (all environments)
- **Notifications:** AWS SES, Microsoft Teams, Slack
- **Code Quality:** ruff, mypy, pytest

---

## ✅ Design Decisions Status

**All critical design decisions finalized on 2026-02-14!**

- [x] **Verification detection method** - Tiered: Hash-based + Timestamp, auto-detect
- [x] **Contact-less records** - Notify campaign owner at cycle start
- [x] **Cycle overlap** - Validation at creation + Skip at runtime
- [x] **Notification channels** - Email-only for MVP, extensible architecture
- [x] **Scheduler choice** - EventBridge for all environments
- [x] **Database** - PostgreSQL with async SQLAlchemy
- [x] **All deferred questions** - Simple MVP approaches chosen

See [decisions.md](decisions.md) for complete details of all 12 decisions.

---

## Document Changelog

### 2026-02-14 - Design Decisions Finalized & Verification Strategy
- **All 12 design decisions made and documented**
- Decision #10: Azure AD OAuth2 with App Roles
- Decision #12: Fresh contact lookup at each escalation
- Verification strategy: ECHO provides API and simple page
- Verification Portal Kit defined as separate optional product
- Created [verification-portal-kit.md](verification-portal-kit.md)
- Platform Campaign (dogfooding) documented
- Updated [implementation-plan.md](implementation-plan.md) with verification architecture
- Ready for implementation Phase 1

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

## ✅ Next Steps

1. ~~**Review all design documents**~~ ✅ Complete
2. ~~**Resolve critical open questions**~~ ✅ Complete (all 11 decisions made)
3. ~~**Validate feasibility**~~ ✅ Complete (system is achievable)
4. ~~**Finalize MVP scope**~~ ✅ Complete (clear feature set defined)
5. **BEGIN IMPLEMENTATION** → Follow [implementation-plan.md](implementation-plan.md)

**Ready to start Phase 1: Foundation (2-3 weeks)**

---

## Questions or Feedback

- Design questions: Review [06-open-questions.md](06-open-questions.md)
- Architecture concerns: See [02-architecture.md](02-architecture.md)
- Feasibility doubts: Check [05-feasibility-analysis.md](05-feasibility-analysis.md)
- Implementation details: Consult [implementation-plan.md](implementation-plan.md)
