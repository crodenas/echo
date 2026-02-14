# Design Decisions

This document records all design decisions made for the ECHO project.

**Decision Date:** 2026-02-14
**Status:** All critical decisions finalized, ready for implementation

---

## Critical Decisions (Required for MVP)

### Decision #1: Verification Detection Method

**Question:** How should ECHO determine if a record has been verified?

**Selected Option:** Tiered approach with auto-detection

**Implementation:**

**Tier 0 - Hash-based (Minimum requirement):**
- Calculate SHA256 hash of entire record (excluding `object_id`)
- Compare hash between sync cycles
- Any change = verified
- Zero requirements on data source

**Tier 1 - Timestamp-based (If available):**
- Auto-detect `last_updated` or `last_verified` timestamp fields
- Compare timestamp against cycle start date
- If timestamp >= cycle start = verified

**Auto-detection logic:**
```python
def detect_verification_tier(sample_record):
    if "last_verified" in sample_record:
        return "tier1_verified_timestamp"
    elif "last_updated" in sample_record:
        return "tier1_updated_timestamp"
    else:
        return "tier0_hash_change"
```

**Rationale:**
- Tier 0 removes all barriers to entry (teams start with existing data)
- Tier 1 provides better accuracy when timestamps available
- Auto-detection is user-friendly (smart defaults)
- Hashing entire record is simple for MVP (no field selection)
- Contact change counts as verification (keeps it simple)
- Provides growth path (teams can add timestamps later)

**Implications:**
- Need hash calculation utility (SHA256)
- Need schema detection during campaign creation
- Testing requires mocking various data source structures
- Documentation must explain tiers and trade-offs

**Deferred to Post-MVP:**
- Field selection for hash calculation
- Tier 2 (explicit verification flag)
- Tier 3 (API endpoint for manual verification)
- Upgrade suggestion messaging

---

### Decision #2: Contact-less Records Handling

**Question:** What should happen when a record has no valid contacts?

**Selected Option:** Escalate to campaign owner at cycle start

**Implementation:**
```python
def start_cycle(campaign):
    records = fetch_records_from_source(campaign.data_source)

    # Separate valid vs orphaned
    valid_records = [r for r in records if r.contacts and len(r.contacts) > 0]
    orphaned_records = [r for r in records if not r.contacts or len(r.contacts) == 0]

    # Create cycle with valid records only
    cycle = create_cycle(campaign, valid_records)

    # Immediately notify owner about orphans (if any)
    if orphaned_records:
        send_email(
            to=campaign.owner_email,
            subject=f"[ECHO] {len(orphaned_records)} orphaned records",
            body=render_template("orphaned_records.html",
                                records=orphaned_records,
                                cycle=cycle)
        )

    return cycle
```

**Campaign configuration:**
```python
{
  "owner_email": "alice@example.com",  # Receives orphan notifications
  ...
}
```

**Rationale:**
- Simple to implement (filter and email immediately)
- No storage needed (don't track orphans across escalations)
- Immediate feedback (owner knows at cycle start)
- Clear responsibility (campaign owner handles data quality)
- One email per cycle (orphans don't change during cycle)

**Implications:**
- Campaign model needs `owner_email` field
- Need orphaned records email template
- Orphaned records excluded from cycle (not stored)
- Documentation should guide owners on fixing source data

**Deferred to Post-MVP:**
- Fallback contacts configuration
- Real-time alerts vs. cycle-start summary
- Team/group owner emails
- Orphan tracking history

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

**Selected Option:** Campaign-level channel configuration with extensible architecture

**Implementation:**

**MVP - Email Only:**
```python
# Campaign configuration
{
  "name": "Q1 Service Verification",
  "notification_channels": {
    "email": {
      "enabled": true,
      "template_id": "custom_email_template_v2",
      "from_address": "noreply@echo.example.com"
    }
  },
  "default_channel": "email"
}
```

**Extensible Architecture:**
```python
# Channel Protocol
class NotificationChannel(Protocol):
    def send(self, recipient, records, campaign, template) -> NotificationResult: ...
    def validate_recipient(self, recipient) -> bool: ...

# Email Implementation (MVP)
class EmailChannel:
    def send(self, recipient, records, campaign, template):
        # Render and send email
        ...

# Future: Teams, Slack
# class TeamsChannel: ...
# class SlackChannel: ...

# Channel Registry
AVAILABLE_CHANNELS = {
    "email": EmailChannel(),
    # "teams": TeamsChannel(),  # Post-MVP
    # "slack": SlackChannel(),   # Post-MVP
}
```

**Template Management:**
```python
# Template model
{
  "template_id": "custom_email_template_v2",
  "channel_type": "email",
  "campaign_id": "campaign-123",
  "subject": "Please verify your resources",
  "body_html": "<html>...</html>",
  "body_text": "Plain text fallback..."
}
```

**Rationale:**
- Email-only for MVP keeps implementation simple
- Protocol-based design makes adding channels trivial
- Campaign owner provides templates (controls messaging)
- Extensible structure supports future channels
- Each channel can have channel-specific config

**Implications:**
- Implement NotificationChannel protocol
- Implement EmailChannel with SES
- Template storage and management needed
- Campaign owner must provide email template

**Deferred to Post-MVP:**
- Microsoft Teams channel implementation
- Slack channel implementation
- User preference system (choose preferred channel)
- Multi-channel per campaign (email + Teams)
- Fallback channel logic

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
  "campaign_schedule": "cron(0 0 1 * ? *)",  # Monthly (outer: start new wave)
  "escalation_rules": [                      # Inner: escalations within wave
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
| **Viewer** | `echo.viewer` | Read-only access to campaigns and waves | Entra group: `ECHO-Viewers` |

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

**Question:** When should contacts be resolved - at wave start (snapshot) or at each escalation (fresh lookup)?

**Selected Option:** Fresh lookup at each escalation

**Implementation:**
```python
def execute_escalation(wave_id: str, escalation_level: int):
    """Execute escalation with fresh data from source."""

    # Re-query data source at each escalation
    source_records = fetch_from_data_source(campaign.data_source)

    # Check verification status (might be verified now)
    unverified = [r for r in source_records if not is_verified(r, wave.start_date)]

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
- **Auto-stops on verification** - If verified mid-wave, subsequent escalations detect it
- **Simpler data model** - No need to store enriched contact snapshots
- **Practical** - Can't notify departed employees anyway

**Known Behavior: Contact Changes Mid-Wave**

If contacts change during a wave, the new contact inherits the current escalation level:

**Example:**
```
Day 0 (Wave Start):
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
| Snapshot at wave start | Original owner accountable | May notify departed/wrong people | ❌ Rejected |
| Track changes, reset escalation | New owner starts fresh | Wave may never complete; complex | ❌ Too complex |
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

## Summary

### All Decisions at a Glance

| # | Question | MVP Decision | Deferred |
|---|----------|--------------|----------|
| 1 | Verification Detection | Tier 0 (hash) + Tier 1 (timestamp), auto-detect | Field selection, Tier 2/3, upgrade messaging |
| 2 | Contact-less Records | Notify owner at cycle start | Fallback contacts, tracking history |
| 3 | Cycle Overlap | Validation + Skip | Auto-adjustment, advanced handling |
| 4 | Multi-Channel | Email-only, extensible architecture | Teams, Slack, user preferences |
| 5 | Notification Frequency | Configurable per escalation | Business hours, smart escalation |
| 6 | Scheduler | EventBridge (dev and prod) | Mock scheduler, cross-region |
| 7 | Database | PostgreSQL | Partitioning, read replicas |
| 8 | Template System | Jinja2 in campaign JSONB | Database templates, editor UI |
| 9 | Campaign Modes | Unified flexible model | Specialized modes if needed |
| 10 | Authentication | Azure AD OAuth2 (single tenant) | RBAC via groups, multi-tenancy, delegation |
| 11 | Audit Logging | Standard Python logging | Immutable audit table, compliance |
| 12 | Contact Resolution Timing | Fresh lookup at each escalation | Contact change detection, escalation reset |
| 13 | Employee Directory Integration | Azure REST API with SystemId lookups | Employee caching, alt formats, preferences |

### Key Technical Choices

- **Language:** Python 3.13+
- **Framework:** FastAPI (async)
- **Database:** PostgreSQL with SQLAlchemy 2.0 (async)
- **Scheduler:** AWS EventBridge (all environments)
- **Notifications:** Email via AWS SES (MVP)
- **Templates:** Jinja2 (filesystem)
- **Package Manager:** uv
- **Code Quality:** ruff, mypy, pytest

### Ready for Implementation

All critical decisions are finalized. The design is:
- ✅ **Simple** - MVP focuses on core features
- ✅ **Extensible** - Architecture supports future enhancements
- ✅ **Practical** - Leverages existing tools and patterns
- ✅ **Achievable** - 12-14 week timeline for MVP

**Next Step:** Begin Phase 1 implementation (Foundation)
