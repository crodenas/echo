# Design Decisions

This document records all design decisions made for the ECHO project.

**Decision Date:** 2026-02-14
**Last Updated:** 2026-02-15 (MVP Simplifications)
**Status:** Simplified for MVP - ready for implementation

---

## Critical Decisions (Required for MVP)

### Decision #1: Verification Detection Method

**Question:** How should ECHO determine if a record has been verified?

**Selected Option (MVP):** Require `last_verified` timestamp field

**UPDATED 2026-02-15:** Simplified from two-tier approach to single timestamp requirement for MVP.

**Implementation:**

**Data Source Requirement:**
```sql
-- Data source MUST include last_verified timestamp
CREATE VIEW echo_services_view AS
SELECT
  service_id AS object_id,              -- Required
  last_verified_date AS last_verified,  -- Required (timestamp)
  owner_system_id AS owner,             -- Required (contact)
  service_name AS name,                 -- Optional
  description                           -- Optional
FROM services;
```

**Validation at Campaign Creation:**
```python
def validate_data_source(data_source_config):
    """Validate that data source has required fields."""
    sample = fetch_sample_record(data_source_config)

    if "object_id" not in sample:
        raise ValidationError("Data source must include 'object_id' field")

    if "last_verified" not in sample:
        raise ValidationError(
            "Data source must include 'last_verified' timestamp field. "
            "Add this to your SQL view or use an existing timestamp field."
        )

    # Check for at least one contact field
    contact_fields = [k for k in sample.keys()
                     if k not in ["object_id", "last_verified", "name", "description"]]
    if not contact_fields:
        raise ValidationError("Data source must include at least one contact field")
```

**Verification Logic (Simple):**
```python
def is_verified(record: dict, cycle_start_date: datetime) -> bool:
    """Check if record was verified since cycle started."""
    last_verified = record.get("last_verified")

    if not last_verified:
        return False  # Never verified

    return last_verified >= cycle_start_date
```

**Rationale:**
- **Much simpler implementation** - Single code path, no hash logic
- **Clear requirement** - Teams know they need to add timestamp field
- **Better semantics** - Timestamp is more meaningful than "any change"
- **Easier testing** - One verification method to test
- **Most teams can comply** - Easy to add timestamp field to views
- **Faster to market** - Saves ~1 week of implementation time

**What Teams Need to Do:**
```sql
-- Option 1: Use existing timestamp
SELECT
  service_id AS object_id,
  updated_at AS last_verified  -- Repurpose existing field
FROM services;

-- Option 2: Add new field (starts NULL = "never verified")
ALTER VIEW echo_services_view
  ADD COLUMN last_verified TIMESTAMP DEFAULT NULL;

-- Option 3: Use current timestamp as starting point
SELECT
  service_id AS object_id,
  CURRENT_TIMESTAMP AS last_verified  -- Everyone starts "verified"
FROM services;
```

**Implications:**
- Teams must be able to modify their data source (add/rename field)
- Teams with truly immutable data sources cannot use MVP
- Single verification code path (simpler, faster)
- No hash storage needed (smaller database)

**Deferred to MVP+:**
- **Tier 0 (Hash-based verification)** - For data sources without timestamps
- Auto-detection of timestamp fields (just require `last_verified` for MVP)
- Alternative field names support (`last_updated`, `verified_date`, etc.)
- Explicit verification API endpoint

---

### Decision #2: Contact-less Records Handling

**Question:** What should happen when a record has no valid contacts?

**Selected Option (MVP):** Skip and log (simplified)

**UPDATED 2026-02-15:** Simplified to just log warnings for MVP.

**Implementation:**
```python
async def execute_escalation(cycle_id: str, escalation_level: int):
    """Execute escalation, skip records without contacts."""

    records = await fetch_from_source()

    for record in records:
        # Skip records without contacts
        if not has_valid_contacts(record):
            logger.warning(
                f"Skipping record {record['object_id']} - no valid contacts",
                extra={
                    "cycle_id": cycle_id,
                    "record_id": record["object_id"],
                    "campaign_id": campaign.id
                }
            )
            continue

        # Process normally
        ...
```

**Rationale:**
- **Simplest implementation** - No email workflow needed
- **CloudWatch visibility** - Warnings visible in logs
- **No extra templates** - One less email template to maintain
- **Campaign owner can check logs** - If they care about orphans
- **Defers complexity** - Can add notifications later if needed

**Implications:**
- Records without contacts are silently skipped (logged only)
- Campaign owners should monitor CloudWatch logs if concerned
- No proactive notification about data quality issues
- Documentation should mention this behavior

**Deferred to MVP+:**
- Email notifications to campaign owner about orphaned records
- Orphaned records summary report
- Fallback contact configuration
- Orphan tracking history
- Dashboard showing orphaned record counts

---

### Decision #3: Cycle Overlap Management

**Question:** What happens if a new campaign cycle starts before the previous one completes?

**Selected Option:** Validation + Skip (two-layer protection)

**Implementation:**

**Layer 1 - Validation at Campaign Creation:**
```python
def validate_campaign_schedule(campaign_data):
    # Calculate estimated cycle duration
    max_delay = max(rule.delay_days for rule in campaign_data.escalation_rules)
    estimated_cycle_duration = max_delay + 1  # +1 day buffer

    # Parse campaign frequency from AWS cron
    frequency_days = estimate_frequency_from_cron(campaign_data.campaign_schedule)

    # Validate
    if frequency_days <= estimated_cycle_duration:
        raise ValidationError(
            f"Campaign frequency ({frequency_days} days) must exceed "
            f"cycle duration ({estimated_cycle_duration} days). "
            f"Increase campaign frequency or reduce escalation delays."
        )
```

**Layer 2 - Runtime Safety Check:**
```python
def trigger_new_cycle(campaign_id):
    campaign = get_campaign(campaign_id)

    # Check for active cycle
    active_cycle = get_active_cycle(campaign_id)

    if active_cycle:
        logger.warning(f"Skipping cycle - previous cycle still active")

        # Notify owner
        send_email(
            to=campaign.owner_email,
            subject=f"[ECHO] Cycle skipped: {campaign.name}",
            body="Previous cycle still running. Consider adjusting schedule."
        )

        return None  # Don't create new cycle

    # Safe to proceed
    return create_new_cycle(campaign)
```

**Rationale:**
- Prevention at creation time catches misconfiguration early
- Runtime check provides defensive safety net
- Skip behavior is safest (no data loss, no confusion)
- Owner notification provides visibility and feedback
- Simple logic (no parallel cycles or force-complete)

**Implications:**
- Need cron-to-days estimation utility
- Need validation in campaign creation endpoint
- Need active cycle check in scheduler trigger
- Need email template for skip notification

**Deferred to Post-MVP:**
- Automatic schedule adjustment suggestions
- Cycle duration prediction based on history
- Advanced overlap handling strategies

---

### Decision #4: Multi-Channel Notification Strategy

**Question:** How should multiple notification channels be handled?

**Selected Option (MVP):** Email only, direct implementation (no abstraction)

**UPDATED 2026-02-15:** Simplified to direct email implementation for MVP.

**Implementation:**

**Campaign Configuration:**
```python
{
  "name": "Q1 Service Verification",
  "email_template_name": "default"  # Simple: just template name
}
```

**Email Service (Direct Implementation):**
```python
# src/services/email_service.py
class EmailService:
    def __init__(self):
        self.ses_client = boto3.client('ses')
        self.template_env = Environment(loader=FileSystemLoader('src/templates/email'))

    async def send_notification(
        self,
        recipient_email: str,
        recipient_name: str,
        records: list[dict],
        campaign: Campaign,
        escalation_level: int
    ):
        """Send email notification via AWS SES."""

        # Load and render template
        template = self.template_env.get_template(f"{campaign.email_template_name}.html")
        html_body = template.render(
            recipient={"email": recipient_email, "name": recipient_name},
            campaign=campaign,
            records=records,
            escalation_level=escalation_level
        )

        # Send via SES
        self.ses_client.send_email(
            Source=settings.email_from_address,
            Destination={"ToAddresses": [recipient_email]},
            Message={
                "Subject": {"Data": f"[ECHO] {campaign.name} - Verification Required"},
                "Body": {"Html": {"Data": html_body}}
            }
        )
```

**Templates (Jinja2 Files):**
```
src/templates/email/
├── default.html      # Default template
└── (custom templates can be added as files)
```

**Rationale:**
- **Simplest possible implementation** - Direct SES integration
- **No abstraction overhead** - No protocol, no registry, no factory
- **Faster to implement** - ~3-5 days saved
- **Email is sufficient** - Proves value without complexity
- **Easy to extend later** - Can add abstraction when actually needed

**Implications:**
- No NotificationChannel protocol (YAGNI for MVP)
- Templates are files only (no database storage)
- Campaign just stores template name (string field)
- Direct boto3 SES calls

**Deferred to MVP+:**
- NotificationChannel protocol abstraction
- Microsoft Teams channel implementation
- Slack channel implementation
- User preference system (choose preferred channel)
- Multi-channel per campaign (email + Teams)
- Fallback channel logic
- Database-stored custom templates

---

### Decision #5: Execution Model

**Question:** How should escalations be executed? Isolated containers or in-process jobs?

**Selected Option (MVP):** Per-escalation ECS Fargate tasks, launched directly by EventBridge

**UPDATED 2026-02-18:** Revised from background jobs to isolated Fargate tasks. Workers use a lazy scheduling pattern — each worker creates the next escalation schedule only if unverified records remain.

**Architecture:**
```
EventBridge (campaign schedule, recurring)
  ↓ POST /internal/start-cycle/{campaign_id}
Echo API (containerized ECS service, always running)
  → Creates Cycle record in DB
  → Creates escalation-0 schedule only (lazy — not all upfront)
  ↓
EventBridge (escalation-0 schedule, one-time)
  ↓ Launches ECS Fargate task directly
Worker Container (ephemeral)
  → Queries data source (fresh lookup)
  → Checks verification status at runtime
  → Sends notifications
  → If unverified_count > 0: creates escalation-1 schedule
  → Terminates
  ↓
[N days later — if records still unverified]
EventBridge (escalation-1 schedule, one-time)
  ↓ Launches new ECS Fargate task directly
Worker Container (ephemeral)
  → ... same pattern, creates escalation-2 schedule if needed
  → Terminates
```

**Lazy Scheduling Pattern:**
```python
# src/workers/cycle_worker.py

async def execute_escalation(cycle_id: str, level: int):
    """Execute escalation in isolated container."""

    cycle = await get_cycle(cycle_id)
    campaign = await get_campaign(cycle.campaign_id)

    # Fresh lookup from data source at runtime
    all_records = await fetch_from_data_source(campaign.data_source)

    # Evaluate verification status at runtime
    unverified = [r for r in all_records if not is_verified(r, cycle.start_date)]

    if not unverified:
        # Everything verified — cycle complete
        await mark_cycle_complete(cycle_id)
        logger.info(f"Cycle {cycle_id} complete — all records verified")
        return

    # Send notifications for this escalation level
    await send_notifications(unverified, campaign, cycle, level)

    # Schedule next escalation if one exists
    next_level = level + 1
    next_rule = get_escalation_rule(campaign, next_level)

    if next_rule:
        # Deterministic schedule name (idempotent on retry)
        schedule_name = f"cycle-{cycle_id}-esc-{next_level}"
        trigger_at = cycle.start_date + timedelta(days=next_rule.delay_days)

        await create_escalation_schedule(
            name=schedule_name,
            trigger_at=trigger_at,
            cycle_id=cycle_id,
            level=next_level
        )
        await update_cycle(cycle_id, current_escalation_level=next_level)
    else:
        # No more escalations — cycle ends
        await mark_cycle_complete(cycle_id)
```

**Rationale:**
- **Campaign isolation** - Failures in one campaign's worker don't affect others
- **Lazy scheduling** - No unnecessary worker launches if records verified early
- **Clean cancellation** - Cancelling a cycle only requires deleting one pending schedule
- **Natural termination** - Cycle completes as soon as all records are verified
- **Idempotent schedule names** - Safe to retry if worker crashes before creating next schedule
- **EventBridge retries** - Failed task launches retry automatically (up to 2 attempts)

**Implications:**
- Two ECS components: long-running API service + ephemeral worker task definition
- Workers receive `CYCLE_ID` and `ESCALATION_LEVEL` as environment variable overrides
- `current_escalation_level` field needed on Cycle record (for monitoring and recovery)
- EventBridge IAM role requires `ecs:RunTask` permission on worker task definition
- DLQ on EventBridge schedule captures permanently failed launches

**Deferred to MVP+:**
- Recovery job to detect stuck cycles (worker crashed before scheduling next)
- Per-escalation resource limit overrides
- Advanced retry strategies beyond EventBridge defaults

---

### Decision #6: Scheduler Technology Choice

**Question:** What scheduler technology should ECHO use?

**Selected Option:** AWS EventBridge Scheduler (all environments)

**Implementation:**
```python
# Configuration
{
  "dev": {
    "scheduler_group": "dev",
    "aws_region": "us-east-1"
  },
  "prod": {
    "scheduler_group": "prod",
    "aws_region": "us-east-1"
  }
}

# Single EventBridge Implementation
class EventBridgeScheduler:
    def __init__(self):
        self.client = boto3.client('scheduler')
        self.schedule_group = settings.scheduler_group
        self._ensure_group_exists()

    def create_schedule(self, schedule_id, cron_expression, target_arn, metadata=None):
        schedule_name = f"{self.schedule_group}-{schedule_id}"

        self.client.create_schedule(
            Name=schedule_name,
            GroupName=self.schedule_group,  # Environment isolation
            ScheduleExpression=cron_expression,  # AWS cron format
            Target={
                "Arn": target_arn,  # ECS task or Lambda
                "RoleArn": settings.scheduler_role_arn,
                ...
            }
        )
```

**Environment Isolation:**
- `dev` - Development environment (single developer)
- `prod` - Production environment

**Rationale:**
- **Single implementation** - Same code dev and prod (no APScheduler)
- **Dev/prod parity** - Identical behavior in all environments
- **No local complexity** - No need for in-process scheduler
- **AWS cron format** - Standard, no translation needed
- **Free tier** - 14M invocations/month (more than enough)
- **Test against real** - No surprises when deploying to prod

**Implications:**
- AWS credentials required for development
- Developer runs API locally, connects to AWS EventBridge
- Schedule groups provide environment isolation
- All schedules use AWS cron format
- Use `aws-croniter` library for validation

**Deferred to Post-MVP:**
- Schedule cleanup automation
- Cross-region scheduling
- Advanced retry policies

---

### Decision #7: Database Choice

**Question:** Which database technology?

**Selected Option:** PostgreSQL

**Implementation:**
```python
# Configuration (.env)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Dev (AWS RDS)
DATABASE_URL=postgresql+asyncpg://echo:password@echo-dev.rds.amazonaws.com:5432/echo_dev

# Prod (AWS RDS)
DATABASE_URL=postgresql+asyncpg://echo:password@echo-prod.rds.amazonaws.com:5432/echo_prod

# SQLAlchemy 2.0 with async
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(settings.database_url)
async_session = sessionmaker(engine, class_=AsyncSession)
```

**Developer Setup:**
- Developer runs API locally
- Connects to AWS RDS (echo-dev instance)
- No local PostgreSQL container needed

**Schema Features:**
- Relational tables with foreign keys (campaigns → cycles → records)
- JSONB columns for flexible metadata (`source_data`, `notification_channels`)
- Array columns for contacts (`contacts VARCHAR[]`)
- UUID primary keys
- Indexes on foreign keys and frequently queried fields

**Rationale:**
- Perfect fit for relational data model
- JSONB provides flexibility for variable source data
- ACID transactions ensure atomicity
- Rich querying capabilities (joins, aggregations)
- Well-understood scaling patterns
- AWS RDS for all environments (dev and prod)
- Same setup dev and prod (connection string config)

**Implications:**
- SQLAlchemy 2.0 with async/await
- Alembic for migrations
- AWS RDS instance required for dev environment
- Developer connects to AWS RDS (no local containers)

**Deferred to Post-MVP:**
- Table partitioning for large tables
- Read replicas for reporting
- Connection pooling optimization
- Advanced indexing strategies

---

## Deferred Decisions (Post-MVP)

### Decision #5: Notification Frequency Within Cycle

**Question:** How often should notifications be sent during a cycle?

**Selected Option for MVP:** Configurable per escalation (simple)

**Implementation:**
```python
# Campaign configuration
{
  "escalation_rules": [
    {"level": 1, "delay_days": 0, "recipients": ["record_contacts"]},
    {"level": 2, "delay_days": 7, "recipients": ["record_contacts"]},
    {"level": 3, "delay_days": 14, "recipients": ["record_contacts", "team_lead@example.com"]}
  ]
}
```

**Rationale:**
- Simple and predictable
- Campaign owner has full control
- Easy to configure and understand
- Covers most use cases

**Deferred:**
- Business hours awareness (timezone handling)
- Smart escalation (adaptive delays)
- Calendar-based scheduling
- Holiday/weekend skip logic

---

### Decision #8: Template System

**Question:** How should notification templates be managed?

**Selected Option for MVP:** Jinja2 templates in files

**Implementation:**
```
src/templates/
├── email/
│   ├── default.html          # Default email template
│   └── default.txt           # Plain text fallback
└── (future: teams/, slack/)
```

```python
# Load template from filesystem
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('src/templates'))
template = env.get_template('email/default.html')

# Render with data
html = template.render(
    recipient=recipient,
    records=records,
    campaign=campaign
)
```

**Rationale:**
- Simplest to implement
- Version controlled (git)
- Easy to edit (just files)
- Good enough for MVP

**Deferred:**
- Database-stored custom templates
- Per-campaign template overrides
- Template editor UI
- Template versioning and rollback
- Hybrid approach (defaults in files, overrides in DB)

---

### Decision #9: Campaign Modes (SVT, AVT, CVT)

**Question:** Should we implement different campaign "modes"?

**Selected Option for MVP:** Unified flexible model (single campaign type)

**Implementation:**
```python
# All campaigns use same Campaign model
# Use cases emerge from configuration

# SVT (Standard Verification) - Regular intervals
{
  "campaign_schedule": "cron(0 0 1 * ? *)",  # Monthly (outer: start new cycle)
  "escalation_rules": [                      # Inner: escalations within cycle
    {"level": 1, "delay_days": 0},
    {"level": 2, "delay_days": 7},
    {"level": 3, "delay_days": 14}
  ]
}

# AVT (Automated Verification) - Same as SVT
# (No difference in MVP - both just use schedules)

# CVT (Contact Validation) - Filter for missing contacts
# (Handled automatically - orphaned records go to owner)
```

**Rationale:**
- Simpler codebase (one campaign type)
- More flexible (not locked into modes)
- Use cases can emerge from configuration
- Avoid premature abstraction

**Deferred:**
- Specialized campaign modes if needed
- Mode-specific UI or wizards
- Mode-specific validation rules
- Template suggestions per mode

---

### Decision #10: Authentication and Authorization

**Question:** How should users authenticate to ECHO?

**Selected Option:** Microsoft Azure OAuth2 (Azure AD / Entra ID)

**Implementation:**

**Authentication Flow:**
```python
# FastAPI middleware validates Azure AD OAuth2 tokens
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize",
    tokenUrl=f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate Azure AD token and extract user identity."""

    # Validate JWT token
    payload = validate_azure_token(token, TENANT_ID, CLIENT_ID)

    # Extract user info from claims
    user = {
        "email": payload["preferred_username"],  # alice@company.com
        "name": payload["name"],                  # Alice Smith
        "object_id": payload["oid"],              # Azure AD user object ID
        "roles": payload.get("roles", [])         # App Roles (echo.admin, echo.campaign_owner, etc.)
    }

    return user

# Authorization helpers
def require_role(required_role: str):
    """Dependency to require specific app role."""
    def role_checker(user = Depends(get_current_user)):
        if required_role not in user["roles"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

# Use in endpoints
@app.post("/api/campaigns")
async def create_campaign(
    campaign: CampaignCreate,
    user = Depends(get_current_user)
):
    campaign.created_by = user["email"]
    campaign.owner_email = user["email"]  # Default to creator
    ...
```

**Environment Configuration:**

| Environment | AWS Account | Azure App Registration | Tenant |
|-------------|-------------|------------------------|--------|
| **Dev** | dev-account | echo-dev | company-tenant |
| **QA** (optional) | qa-account | echo-qa | company-tenant |
| **Prod** | prod-account | echo-prod | company-tenant |
| **Developer Sandbox** | Local Docker | echo-dev (shared) | company-tenant |

**App Registration Setup:**
- Single tenant (company Azure AD)
- Separate app registration per environment
- Redirect URIs configured for each environment
- API permissions: User.Read, email, profile
- Token validation: audience, issuer, signature

**App Roles Definition:**

Each app registration defines the following app roles:

| Role | Value | Description | Assigned To |
|------|-------|-------------|-------------|
| **ECHO Admin** | `echo.admin` | Full system access, manage all campaigns | Entra group: `ECHO-Admins` |
| **Campaign Owner** | `echo.campaign_owner` | Create and manage own campaigns | Entra group: `ECHO-Users` |
| **Viewer** | `echo.viewer` | Read-only access to campaigns and cycles | Entra group: `ECHO-Viewers` |

**App Role Assignment:**
```
Azure AD Groups → App Roles → Users

Example:
  User: alice@company.com
    ↓ Member of
  Entra Group: ECHO-Users
    ↓ Assigned to
  App Role: echo.campaign_owner
    ↓ Included in
  JWT Token: "roles": ["echo.campaign_owner"]
```

**Authorization in Endpoints:**
```python
# Admin-only endpoint
@app.delete("/api/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    user = Depends(require_role("echo.admin"))
):
    # Only admins can delete campaigns
    ...

# Campaign owner can edit own campaigns
@app.put("/api/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    updates: CampaignUpdate,
    user = Depends(get_current_user)
):
    campaign = get_campaign(campaign_id)

    # Check ownership or admin role
    if campaign.owner_email != user["email"] and "echo.admin" not in user["roles"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Update campaign
    ...

# Viewers can read
@app.get("/api/campaigns")
async def list_campaigns(user = Depends(get_current_user)):
    # Any authenticated user can list (enforced by OAuth2)
    # Filter based on role
    if "echo.admin" in user["roles"] or "echo.viewer" in user["roles"]:
        return get_all_campaigns()  # Admin/viewers see all
    else:
        return get_campaigns_owned_by(user["email"])  # Others see own campaigns
```

**Developer Sandbox:**
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    # ... postgres config

  api:
    # Use dev app registration
    environment:
      - AZURE_TENANT_ID=${AZURE_TENANT_ID}
      - AZURE_CLIENT_ID=${AZURE_CLIENT_ID}  # echo-dev
      - AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}
```

**Campaign Ownership:**
```python
# Campaign model
{
  "owner_email": "alice@example.com",     # Campaign owner (can edit)
  "created_by": "alice@example.com",      # Who created it
  "created_by_oid": "abc-123-def",        # Azure AD object ID
  ...
}

# Authorization check
def user_can_edit_campaign(campaign, user):
    return campaign.owner_email == user["email"]
```

**Rationale:**
- Company already uses Azure AD (single source of truth)
- OAuth2 is industry standard
- No password management needed
- Seamless integration with company directory
- App Roles provide clean, application-specific RBAC
- Roles assigned to Entra groups (centralized access management)
- Roles included in JWT token automatically

**MVP Scope:**
- ✅ Azure AD OAuth2 token validation
- ✅ User identity from JWT claims
- ✅ App Roles definition (admin, campaign_owner, viewer)
- ✅ App Roles assigned to Entra groups
- ✅ Role-based authorization in API endpoints
- ✅ Campaign ownership (creator = owner)
- ✅ Authorization checks (owner + admin can edit)
- ✅ App registrations per environment

**Deferred to Post-MVP:**
- Multi-tenancy (team isolation)
- Delegated access (share campaigns with other users)
- Fine-grained permissions (per-campaign ACLs)
- Service principal auth (for automation/CI/CD)
- Token refresh handling in UI
- Audit trail of who accessed what

---

### Decision #11: Audit and Compliance

**Question:** What level of audit logging is needed?

**Selected Option for MVP:** Standard Python logging

**Implementation:**
```python
# Use Python's logging module
import logging

logger = logging.getLogger(__name__)

# Log important events
logger.info(f"Campaign created: {campaign.id} by {campaign.owner_email}")
logger.info(f"Cycle started: {cycle.id} for campaign {campaign.id}")
logger.info(f"Notification sent to {recipient} via {channel}")
logger.warning(f"Orphaned records found: {len(orphaned)}")
logger.error(f"Scheduler error: {error}")

# Configure output
# Dev: Console
# Prod: CloudWatch Logs
```

**Rationale:**
- Built-in to Python
- Good enough for MVP
- Easy to configure different outputs
- Searchable in CloudWatch

**Deferred:**
- Immutable audit table in database
- Comprehensive audit trail (who, what, when, why)
- Audit log retention policies
- Compliance reporting
- User action tracking
- Data access logs
- Long-term archive to S3

---

### Decision #12: Contact Resolution Timing

**Question:** When should contacts be resolved - at cycle start (snapshot) or at each escalation (fresh lookup)?

**Selected Option:** Fresh lookup at each escalation

**Implementation:**
```python
def execute_escalation(cycle_id: str, escalation_level: int):
    """Execute escalation with fresh data from source."""

    # Re-query data source at each escalation
    source_records = fetch_from_data_source(campaign.data_source)

    # Check verification status (might be verified now)
    unverified = [r for r in source_records if not is_verified(r, cycle.start_date)]

    # Resolve recipients using CURRENT contacts from source
    for record in unverified:
        recipients = resolve_recipients(
            record,
            campaign.contact_mapping,
            escalation_rule.recipients,
            employee_service
        )
        send_notification(recipients, record)
```

**Rationale:**
- **Always accurate** - Notifications go to current responsible parties
- **Handles personnel changes** - If tech lead changes from Bob to Alice, Alice gets notified (not Bob)
- **Auto-stops on verification** - If verified mid-cycle, subsequent escalations detect it
- **Simpler data model** - No need to store enriched contact snapshots
- **Practical** - Can't notify departed employees anyway

**Known Behavior: Contact Changes Mid-Cycle**

If contacts change during a cycle, the new contact inherits the current escalation level:

**Example:**
```
Day 0 (Cycle Start):
  - Service-123 tech_lead = Bob

Day 0 (Escalation 1): ["contact1"]
  - ✅ Notify Bob
  - Bob ignores notification

Day 5:
  - Bob transfers to another team
  - Service-123 tech_lead updated to Alice

Day 7 (Escalation 2): ["contact1", "contact1.manager"]
  - contact1 resolves to Alice (current tech lead)
  - contact1.manager resolves to Alice's manager (David)
  - ✅ Notify Alice
  - ✅ Notify David (Alice's manager, not Bob's!)
```

**Tradeoff:** David gets an escalation notification even though Alice just inherited the record and hasn't had a chance to verify it yet.

**Why this is acceptable:**
- Goal is verification by current owner, not assigning blame
- Escalating to Alice's current manager is more effective than Bob's former manager
- Alternative approaches (snapshot contacts, track changes, reset escalation) add significant complexity
- Campaign owners can monitor contact changes if needed

**Alternatives Considered:**

| Approach | Pro | Con | Decision |
|----------|-----|-----|----------|
| Snapshot at cycle start | Original owner accountable | May notify departed/wrong people | ❌ Rejected |
| Track changes, reset escalation | New owner starts fresh | Cycle may never complete; complex | ❌ Too complex |
| Notify old + new contacts | No one escapes | Spammy; confusing | ❌ Poor UX |
| **Fresh lookup (current)** | **Always accurate; simple** | **New owner inherits escalation** | ✅ **MVP** |

**Implications:**
- Data source must be available at each escalation (transient failures handled by EventBridge retry)
- No `records` table needed - use `cycles.record_hashes` JSONB for Tier 0 verification only
- Fresh contact lookup ensures current owners always notified
- Contacts resolved at escalation time (not snapshotted)

**Deferred to Post-MVP:**
- Contact change detection and notification ("You recently inherited this resource")
- Optional escalation level reset when primary contact changes
- Campaign owner alerts on frequent contact changes
- Template variable: `contact_recently_changed` flag

---

### Decision #13: Employee Directory Integration

**Question:** How should ECHO resolve contact identifiers to employee information and traverse manager hierarchies?

**Selected Option:** Azure-protected Employee REST API with SystemId-based lookups

**CONFIRMED 2026-02-15:** KEEP for MVP - simpler than initially estimated (~1 week, not 2-3 weeks) because we're already implementing Azure AD OAuth2 for the ECHO API (Decision #10). Calling another Azure AD protected API reuses the same authentication pattern.

**Integration Details:**

**Employee API:**
- **Endpoint:** Azure AD protected REST API
- **Authentication:** OAuth 2.0 (using ECHO's Azure AD app registration)
- **Data Refresh:** Every 24 hours (exact time unknown)
- **Data Staleness:** Employee data may be up to 24 hours old
- **Example Data:** See `examples/data/Employees.json`
- **Record Count:** ~1000 employees (test data)

**Employee Record Structure:**
```json
{
  "SystemId": "j2y0092",              // Unique identifier (primary key)
  "GlobalId": 220,                     // Global identifier
  "FirstName": "Rosita",
  "LastName": "Kingstne",
  "InternetEmailAddress": "rkingstne63@creativecommons.org",
  "JobTitle": "Director of Engineering",
  "SupervisorSystemId": "q8r3249"     // Links to supervisor's SystemId (null for CEO)
}
```

**Key Fields:**
- `SystemId`: Primary identifier used in data source contact fields
- `InternetEmailAddress`: Email address for notifications
- `SupervisorSystemId`: Enables manager hierarchy traversal (null for top-level)
- `FirstName`, `LastName`: For personalized notifications

**Contact Resolution Flow:**

```python
class EmployeeService:
    """Resolve contact identifiers and traverse manager hierarchy."""

    async def get_employee(self, system_id: str) -> Employee:
        """Get employee by SystemId."""
        response = await self.http_client.get(
            f"{self.api_url}/employees/{system_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        return Employee(**response.json())

    async def get_manager(self, employee: Employee) -> Employee | None:
        """Get employee's direct manager."""
        if not employee.SupervisorSystemId:
            return None  # Top of hierarchy (CEO)
        return await self.get_employee(employee.SupervisorSystemId)

    async def get_manager_chain(self, system_id: str, levels: int = 1) -> list[Employee]:
        """Get manager hierarchy (for multi-level escalations)."""
        managers = []
        current = await self.get_employee(system_id)

        for _ in range(levels):
            manager = await self.get_manager(current)
            if not manager:
                break
            managers.append(manager)
            current = manager

        return managers
```

**Recipient Resolution Examples:**

```python
# Example 1: Direct contact field
# Record: {"owner": "j2y0092", ...}
# Escalation recipients: ["owner"]
employee = await employee_service.get_employee("j2y0092")
# → Send notification to rkingstne63@creativecommons.org

# Example 2: Manager escalation
# Record: {"owner": "j2y0092", ...}
# Escalation recipients: ["owner", "owner.manager"]
employee = await employee_service.get_employee("j2y0092")
manager = await employee_service.get_manager(employee)
# → Send to rkingstne63@creativecommons.org (Rosita Kingstne)
# → Send to clarnerea@geocities.com (Cortney Larner, CEO)

# Example 3: Multi-level escalation
# Escalation recipients: ["owner", "owner.manager", "owner.manager.manager"]
employee = await employee_service.get_employee("j2y0092")
managers = await employee_service.get_manager_chain("j2y0092", levels=2)
# → Rosita (owner)
# → Cortney (manager)
# → (no manager.manager - Cortney is CEO)
```

**Contact Field Mapping:**

Data sources use `SystemId` values in contact fields:
```json
{
  "object_id": "service-123",
  "name": "Payment API",
  "tech_lead": "j2y0092",           // SystemId
  "product_owner": "o2t9772",       // SystemId
  "last_verified": "2024-01-10"
}
```

Campaign escalation rules reference these fields:
```json
{
  "escalation_rules": [
    {
      "level": 0,
      "delay_days": 0,
      "recipients": ["tech_lead"]                    // → j2y0092
    },
    {
      "level": 1,
      "delay_days": 7,
      "recipients": ["tech_lead", "product_owner"]   // → j2y0092, o2t9772
    },
    {
      "level": 2,
      "delay_days": 14,
      "recipients": ["tech_lead.manager"]            // → q8r3249 (Rosita's manager)
    }
  ]
}
```

**Rationale:**
- **Standard integration** - Leverages existing Azure AD protected employee API
- **Simple lookups** - SystemId provides direct employee record access
- **Efficient hierarchy** - SupervisorSystemId enables O(1) manager lookups
- **Reliable** - Centralized employee data source of truth
- **Scalable** - API handles ~1000 employees easily (can cache if needed)

**Implementation Considerations:**

1. **Caching Strategy:**
   - **Cache Duration:** 12 hours (half of API refresh cycle)
   - **Rationale:** Since Employee API refreshes every 24 hours, aggressive caching doesn't increase staleness
   - **Benefits:** Significantly reduces API calls with minimal staleness impact
   - **Alternative:** Could cache up to 23 hours, or use time-based expiration (e.g., expire at 2 AM daily)
   - **Fresh lookup** (Decision #12) still applies - but "fresh" means "from cache or API"
   - At worst, employee data is 12 hours (cache) + 24 hours (API) = 36 hours stale (acceptable)

2. **Data Staleness Implications:**
   - **Fresh lookup** (Decision #12) is limited by API's 24-hour refresh cycle
   - Recently departed employees may appear in API for up to 24 hours
   - Manager changes may not reflect immediately (up to 24-hour delay)
   - Email delivery will fail for departed employees (acceptable - email bounces)
   - **Mitigation:** Email bounce handling will identify invalid addresses

3. **Error Handling:**
   - Missing SystemId: Log warning, skip that recipient
   - Missing manager: Stop hierarchy traversal gracefully
   - API unavailable: Retry with exponential backoff
   - Invalid employee data: Log error, continue with other recipients
   - Email bounces (departed employees): Log and mark as undeliverable

4. **Performance:**
   - Batch employee lookups when possible (e.g., all recipients for a cycle)
   - Async HTTP calls to employee API
   - Connection pooling for API requests

   **Example Caching Implementation:**
   ```python
   from datetime import datetime, timedelta
   from functools import lru_cache
   import time

   class EmployeeService:
       def __init__(self):
           self.cache = {}  # {system_id: (employee, expiry_time)}
           self.cache_duration = timedelta(hours=12)

       async def get_employee(self, system_id: str) -> Employee:
           """Get employee with 12-hour cache."""
           # Check cache
           if system_id in self.cache:
               employee, expiry = self.cache[system_id]
               if datetime.now() < expiry:
                   return employee  # Cache hit (~95% of requests)

           # Cache miss - fetch from API
           employee = await self._fetch_from_api(system_id)

           # Store in cache for 12 hours
           expiry = datetime.now() + self.cache_duration
           self.cache[system_id] = (employee, expiry)

           return employee
   ```

   **Cache Statistics (estimated for typical campaign):**
   - Campaign cycle: 30 days, 3 escalations (day 0, 14, 28)
   - 1000 records, average 2 contacts per record
   - Total API calls without cache: ~6,000 (1000 records × 2 contacts × 3 escalations)
   - Total API calls with 12-hour cache: ~300 (only cache misses/expiries)
   - **API call reduction: 95%**

5. **Security:**
   - Use ECHO's Azure AD service principal for API authentication
   - Store API credentials in AWS Systems Manager Parameter Store
   - Never expose employee data in notifications (only use for routing)

**API Configuration:**

```python
# .env
EMPLOYEE_API_URL=https://employee-api.company.com/api
EMPLOYEE_API_TENANT_ID=your-tenant-id
EMPLOYEE_API_CLIENT_ID=echo-service-principal-id
EMPLOYEE_API_CLIENT_SECRET_PARAM=/echo/integrations/employee-api/client-secret
```

**Deferred to Post-MVP:**
- Employee data synchronization/caching in ECHO database
- Support for alternative contact identifier formats (email instead of SystemId)
- Manager hierarchy depth limits and cycle detection
- Employee directory UI in ECHO admin portal
- Notification preferences from employee API

**Future Optimization:**
- If Employee API refresh time becomes known (e.g., "2 AM daily"), align cache expiration
- Could cache for full 24 hours with daily expiration at known refresh time
- Would achieve near-100% cache hit ratio while guaranteeing same-day freshness

---

### Decision #14: Data Source Types

**Question:** Which data source types should MVP support?

**Selected Option (MVP):** PostgreSQL only

**ADDED 2026-02-15:** Simplified to single data source type for MVP.

**Implementation:**

**PostgreSQL Connector (Only):**
```python
# src/integrations/data_sources/postgresql.py
class PostgreSQLDataSource:
    """PostgreSQL data source connector."""

    def __init__(self, connection_param: str, query: str):
        self.connection_param = connection_param  # Parameter Store path
        self.query = query

    async def fetch_records(self) -> list[dict]:
        """Execute query and return all records."""

        # Fetch connection string from Parameter Store
        connection_string = get_connection_string(self.connection_param)

        # Execute query
        conn = await asyncpg.connect(connection_string)
        try:
            rows = await conn.fetch(self.query)
            return [dict(row) for row in rows]
        finally:
            await conn.close()
```

**Campaign Configuration:**
```python
{
  "data_source": {
    "type": "postgresql",  # Only option for MVP
    "connection_string": "postgresql://user:pass@host:5432/db",
    "query": "SELECT * FROM echo_services_view"
  }
}
```

**Rationale:**
- **Focus on one connector done well** - Better than multiple half-built connectors
- **Most common enterprise database** - PostgreSQL is widely used
- **ECHO uses PostgreSQL** - Dogfooding (can query own database)
- **Easy to create views** - Teams can create dedicated views for ECHO
- **Faster to implement** - Single connector with good error handling
- **Proves core value** - Doesn't need multiple sources to be useful

**Implications:**
- Only PostgreSQL data sources supported
- Teams with other databases must create proxy/wrapper
- Or wait for their database type in MVP+

**Deferred to MVP+:**
- MySQL/MariaDB connector
- REST API connector
- HTTP endpoint connector
- GraphQL connector
- CSV/file-based connector
- Oracle, SQL Server, etc.

---

### Decision #16: Notification Delivery Pattern

**Question:** Should workers send notifications directly, or write to an outbox for a separate dispatcher to send?

**Selected Option (MVP):** Direct send from workers

**Date:** 2026-02-18

**Implementation (MVP):**
```
Worker (Campaign A, Escalation 1)
  → Groups unverified records by recipient
  → Sends one email per recipient containing all their records
  → alice@company.com receives: [service-1, service-2]

Worker (Campaign B, Escalation 1, same day)
  → alice@company.com receives: [database-7]
```
Alice gets two separate emails if she appears in two campaigns on the same day.

**Deferred Option — Outbox Pattern (MVP+):**
```
Worker (Campaign A) → writes to outbox: {recipient: alice, records: [...], campaign: A}
Worker (Campaign B) → writes to outbox: {recipient: alice, records: [...], campaign: B}

Dispatcher (runs daily at 9am)
  → Reads outbox, groups by recipient
  → alice receives ONE email across all campaigns: [service-1, service-2, database-7]
```

**Outbox Schema (when implemented):**
```sql
CREATE TABLE notification_outbox (
    id          UUID PRIMARY KEY,
    recipient   VARCHAR(255) NOT NULL,   -- email address
    campaign_id UUID REFERENCES campaigns(id),
    cycle_id    UUID REFERENCES cycles(id),
    escalation_level INT NOT NULL,
    records     JSONB NOT NULL,          -- records needing verification
    created_at  TIMESTAMP NOT NULL,
    dispatched_at TIMESTAMP              -- NULL = pending
);
```

**Open Question for MVP+ — Mixed Record Types in Digest:**

When the outbox aggregates across campaigns, a recipient may have records from different campaigns with different schemas and different templates:

- Campaign A records: `{service_id, tech_lead, environment}`
- Campaign B records: `{db_instance_id, dba_owner, criticality}`

Options when this happens:
- **Option A: Per-campaign sections** — One email with separate sections per campaign, each rendered with its own template. Clean but complex to compose.
- **Option B: Generic digest template** — Outbox dispatcher uses a single generic template that renders any record type. Loses campaign-specific formatting.
- **Option C: Per-campaign emails, same dispatch window** — Dispatcher still sends one email per campaign per recipient, but batches sends within a time window to avoid immediate back-to-back emails.

Option C is likely the simplest path — it retains per-campaign templates and avoids the mixed-type problem entirely, while still smoothing out notification timing.

**Rationale for deferring:**
- Direct send is sufficient to prove value for MVP
- Outbox adds meaningful complexity (dispatcher service, outbox table, dispatch scheduling)
- Mixed record type problem needs more thought before committing to a design
- Single-campaign deployments won't benefit from cross-campaign grouping

**Deferred to MVP+:**
- Outbox table and dispatcher service
- Cross-campaign digest emails
- User-level daily digest preference
- Configurable dispatch time (e.g. send at 9am recipient's timezone)
- Resolution of mixed record type template strategy

---

### Decision #15: Terminology — Campaign Execution Instance

**Question:** What do we call a single execution instance of a campaign?

**Selected Option:** Cycle

**Date:** 2026-02-18

**Rationale:**
- "Wave" was used informally in early design discussions but never formally adopted
- "Cycle" is more precise — it reflects the recurring, scheduled nature of campaign execution
- "Cycle" is already the term used in `01-core-concepts.md` and throughout the data model
- Avoids confusion with "wave" as used in other contexts (e.g., deployment waves, marketing waves)

**Implications:**
- All documentation, code, and API endpoints use "cycle" (not "wave")
- Database table: `cycles`
- API routes: `/api/cycles`, `/internal/start-cycle/{campaign_id}`
- Worker env var: `CYCLE_ID`
- Any prior references to "wave" in docs or code are considered errors to be corrected

---

## Summary

### All Decisions at a Glance (UPDATED 2026-02-18)

| # | Question | MVP Decision | Deferred |
|---|----------|--------------|----------|
| 1 | Verification Detection | **Require `last_verified` timestamp** | Hash-based (Tier 0), auto-detection |
| 2 | Contact-less Records | **Skip and log (simplified)** | Owner notifications, tracking history |
| 3 | Cycle Overlap | Validation + Skip | Auto-adjustment, advanced handling |
| 4 | Multi-Channel | **Email only, direct implementation** | Protocol abstraction, Teams, Slack |
| 5 | Execution Model | **Per-escalation ECS Fargate tasks, lazy scheduling** | Recovery job for stuck cycles |
| 6 | Scheduler | EventBridge (all environments) | Cross-region, advanced retry |
| 7 | Database | PostgreSQL | Partitioning, read replicas |
| 8 | Template System | Jinja2 files | Database templates, editor UI |
| 9 | Campaign Modes | Unified flexible model | Specialized modes |
| 10 | Authentication | Azure AD OAuth2 | RBAC roles, multi-tenancy |
| 11 | Audit Logging | Standard Python logging | Immutable audit table |
| 12 | Contact Resolution | Fresh lookup at escalation | Contact change detection |
| 13 | Employee Directory | **Azure REST API + `.manager`** ✅ KEEP | Advanced caching, preferences |
| 14 | Data Source Types | **PostgreSQL only** | MySQL, REST API, HTTP, etc. |
| 15 | Terminology | **"Cycle" (not "wave")** | — |
| 16 | Notification Delivery | **Direct send from workers** | Outbox pattern, cross-campaign digest, mixed record types |

**Bold** = Simplified for MVP
✅ = Kept in MVP (complexity manageable)

### Key Technical Choices

- **Language:** Python 3.13+
- **Framework:** FastAPI (async)
- **Database:** PostgreSQL with SQLAlchemy 2.0 (async)
- **Scheduler:** AWS EventBridge (all environments)
- **Notifications:** Email via AWS SES (direct implementation)
- **Templates:** Jinja2 (filesystem)
- **Package Manager:** uv
- **Code Quality:** ruff, mypy, pytest
- **Deployment:** Single ECS service (API + background jobs)

### Simplified MVP Timeline

**Original estimate:** 12-14 weeks
**Simplified estimate:** **8-10 weeks** (~30-40% faster)

**Key Simplifications:**
1. Require `last_verified` timestamp (no hash logic) - **saves 1 week**
2. Skip contact-less records (no owner notification) - **saves 1 day**
3. Email-only (no channel abstraction) - **saves 3-5 days**
4. Background jobs (no per-escalation containers) - **saves 1 week**
5. PostgreSQL only (no multiple connectors) - **saves 3-5 days**

### Ready for Implementation

All MVP decisions finalized. The simplified design is:
- ✅ **Simple** - Core features only, deferred complexity
- ✅ **Extensible** - Clean upgrade path to full vision
- ✅ **Practical** - Proven tools and patterns
- ✅ **Achievable** - **8-10 week timeline for MVP**
- ✅ **Valuable** - Employee directory + manager escalations included

**Next Step:** Begin Phase 1 implementation (Foundation)
