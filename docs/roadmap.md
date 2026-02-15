# ECHO Product Roadmap

**Last Updated:** 2026-02-15
**Status:** MVP in active development

---

## Version Strategy

- **MVP (8-10 weeks):** Core functionality to prove value
- **MVP+ Quick Wins (1-2 weeks each):** High-value features with low complexity
- **MVP+ Medium Features (2-4 weeks each):** Important enhancements
- **Future/Long-term:** Advanced features for scale and enterprise use

---

## MVP - Core Features (Target: 8-10 weeks)

### Campaign Management
- ✅ **Campaign CRUD** - Create, read, update, delete campaigns via REST API
- ✅ **Data Source Validation** - Validate data source has required fields
- ✅ **EventBridge Scheduling** - Automated campaign triggers
- ✅ **Cycle Management** - Automatic cycle creation and tracking
- ✅ **Escalation Scheduling** - Multi-level escalations with configurable delays

### Data Integration
- ✅ **PostgreSQL Data Source** - Single connector, well-implemented
- ✅ **Fresh Data Lookup** - Query source at each escalation
- ✅ **Timestamp Verification** - Require `last_verified` field
- ✅ **Parameter Store Integration** - Secure connection string storage

### Employee Directory
- ✅ **Azure AD Protected API** - OAuth2 integration with Employee API
- ✅ **SystemId Resolution** - Map SystemId to employee email
- ✅ **Manager Chain Traversal** - Support `.manager` syntax
- ✅ **Multi-level Escalations** - `owner.manager.manager` support

### Notifications
- ✅ **Email via AWS SES** - Direct SES integration
- ✅ **Jinja2 Templates** - File-based email templates
- ✅ **Record Grouping** - One email per recipient with all their records
- ✅ **Notification Logging** - Track all sent notifications

### Authentication & Security
- ✅ **Azure AD OAuth2** - User authentication
- ✅ **Campaign Ownership** - Users can only edit their own campaigns
- ✅ **Secure Credentials** - Connection strings in Parameter Store

### Execution & Infrastructure
- ✅ **Single ECS Service** - API + background jobs in one service
- ✅ **FastAPI BackgroundTasks** - Async escalation execution
- ✅ **PostgreSQL Database** - Campaign, cycle, notification storage
- ✅ **CloudWatch Logging** - Standard Python logging

### Developer Experience
- ✅ **REST API** - Full OpenAPI documentation
- ✅ **Automated Testing** - Unit, integration, e2e tests
- ✅ **Local Development** - Run locally, connect to AWS dev resources
- ✅ **Code Quality** - ruff, mypy, pytest

**MVP Success Criteria:**
- First production campaign runs successfully
- Notifications sent to correct recipients
- Manager escalations work (`.manager` syntax)
- Timestamp verification detects changes
- All tests pass

---

## MVP+ Quick Wins (1-2 weeks each)

### Quick Win #1: Hash-Based Verification (Tier 0)
**Effort:** 1 week
**Value:** High - Removes barrier for teams without timestamps

**Features:**
- SHA256 hash calculation of record fields
- Store hashes in `cycles.record_hashes` JSONB
- Auto-detect if `last_verified` missing → use hash
- Any field change = verified

**Why Defer from MVP:**
- Adds complexity (hash calculation, storage, comparison)
- Most teams can add `last_verified` field
- Proves core value without it

---

### Quick Win #2: MySQL Data Source
**Effort:** 3-5 days
**Value:** Medium - Expands supported databases

**Features:**
- MySQL/MariaDB connector
- Similar to PostgreSQL connector
- Connection string validation
- Query execution

**Implementation:**
```python
class MySQLDataSource:
    async def fetch_records(self) -> list[dict]:
        # Similar to PostgreSQL connector
        ...
```

---

### Quick Win #3: REST API Data Source
**Effort:** 1 week
**Value:** High - Support SaaS tools and custom APIs

**Features:**
- HTTP client with authentication (API key, OAuth)
- JSON response parsing
- Pagination support
- Rate limiting

**Example Configuration:**
```json
{
  "data_source": {
    "type": "rest_api",
    "base_url": "https://api.example.com",
    "endpoint": "/services",
    "auth_type": "api_key",
    "api_key_header": "X-API-Key",
    "api_key_value": "secret"
  }
}
```

---

### Quick Win #4: Contact-less Record Notifications
**Effort:** 1-2 days
**Value:** Low-Medium - Better visibility into data quality

**Features:**
- Email campaign owner about orphaned records
- Orphaned records email template
- Summary at cycle start

**Why Defer from MVP:**
- Extra email workflow
- Campaign owners can check CloudWatch logs
- Not critical for core functionality

---

### Quick Win #5: Simple Admin UI
**Effort:** 1-2 weeks
**Value:** Medium - Easier campaign management

**Features:**
- Campaign list view
- Campaign create/edit forms
- Cycle status dashboard
- Notification history viewer
- Simple HTML templates (FastAPI + Jinja2) or basic SPA

**Why Defer from MVP:**
- API is fully functional without UI
- Can use API clients (Postman, curl) initially
- UI is nice-to-have, not required

---

## MVP+ Medium Features (2-4 weeks each)

### Medium #1: Microsoft Teams Channel
**Effort:** 2 weeks
**Value:** High - Popular enterprise communication tool

**Features:**
- Teams webhook or Graph API integration
- Adaptive Card templates
- Mention support (@user)
- Thread-based conversations

**Example Notification:**
```json
{
  "@type": "MessageCard",
  "summary": "Service Verification Required",
  "sections": [{
    "activityTitle": "Q1 Service Verification",
    "facts": [
      {"name": "Records", "value": "5"},
      {"name": "Escalation", "value": "Level 2"}
    ]
  }]
}
```

---

### Medium #2: Slack Channel
**Effort:** 2 weeks
**Value:** Medium-High - Popular for tech teams

**Features:**
- Slack webhook or API integration
- Block Kit templates
- Interactive buttons (verify, dismiss)
- Thread support

---

### Medium #3: NotificationChannel Abstraction
**Effort:** 1 week
**Value:** Low-Medium - Cleaner architecture

**When to Implement:** After adding 2-3 channels (email + Teams + Slack)

**Features:**
- `NotificationChannel` protocol
- Channel registry
- Pluggable channel implementations
- Per-campaign channel selection

**Current:** Direct email implementation
**Future:** Protocol-based with multiple channels

---

### Medium #4: Role-Based Access Control
**Effort:** 2 weeks
**Value:** Medium - Better security for multi-team use

**Features:**
- **Admin role** - Manage all campaigns, delete any campaign
- **Campaign Owner role** - Create and manage own campaigns
- **Viewer role** - Read-only access to campaigns and cycles
- App Roles in Azure AD
- Entra group assignments

**Example:**
```python
@app.delete("/campaigns/{id}")
async def delete_campaign(
    campaign_id: str,
    user = Depends(require_role("echo.admin"))
):
    # Only admins can delete campaigns
    ...
```

---

### Medium #5: Advanced Caching
**Effort:** 1-2 weeks
**Value:** Medium - Better performance at scale

**Features:**
- Employee data caching (12-24 hour TTL)
- Data source query result caching
- Cache invalidation strategies
- Cache hit/miss metrics

**When Needed:** When processing 10k+ records or 100+ campaigns

---

### Medium #6: Verification Portal Kit
**Effort:** 3-4 weeks
**Value:** Medium - For teams without source UI

**Features:**
- Separate deployable application (not part of ECHO)
- Generic data viewing
- Edit forms for record fields
- Calls ECHO verification API
- Customizable per team

**Architecture:**
```
Team's Verification Portal (optional)
  ↓
Reads from data source
  ↓
Provides edit UI
  ↓
Writes to data source
  ↓
Calls ECHO /api/verify endpoint
```

**Why Separate Product:**
- Not all teams need it (many have existing UIs)
- Teams may want heavy customization
- Keeps ECHO focused on orchestration

---

### Medium #7: Platform Campaign
**Effort:** 3-5 days
**Value:** Low-Medium - Dogfooding and demo

**Features:**
- Special campaign that monitors other campaigns
- Queries `campaigns` table
- Notifies owners of stale campaigns
- Self-exclusion logic
- Demonstrates ECHO managing ECHO

**Example:**
```sql
-- Data source query
SELECT
  id::text AS object_id,
  name,
  owner_email AS owner,
  last_run_at
FROM campaigns
WHERE id != :platform_campaign_id  -- Exclude self
  AND last_run_at < NOW() - INTERVAL '90 days'
```

---

## Future / Long-term Features

### Isolation & Reliability

**Per-Escalation ECS Tasks** (4 weeks)
- Each escalation runs in isolated container
- Resource limits per task
- Failure isolation (one campaign doesn't affect others)
- Dead letter queue for permanent failures
- Advanced retry policies

**Why Deferred:**
- Background jobs sufficient for MVP
- Adds infrastructure complexity
- Better isolation but higher operational cost

---

### Advanced Verification

**Explicit Verification API** (2 weeks)
- POST /api/cycles/{id}/records/{id}/verify
- Verification tracking in database
- Simple verification page in ECHO
- Alternative to updating source system

**Field Selection for Hashing** (1 week)
- Configure which fields to include in hash
- Ignore frequently-changing metadata
- More accurate change detection

**Multiple Verification Strategies per Campaign** (2 weeks)
- Combine timestamp + hash + explicit
- Flexible verification logic
- Per-record verification method

---

### Data Sources

**GraphQL Connector** (2 weeks)
- GraphQL query execution
- Variable support
- Fragment support

**HTTP Endpoint Connector** (1 week)
- Simple GET request
- JSON or CSV response
- Minimal authentication

**CSV/File-Based Connector** (1 week)
- S3 file upload
- CSV parsing
- Scheduled file processing

**Oracle, SQL Server, etc.** (1-2 weeks each)
- Additional database connectors
- Database-specific features

---

### Multi-Tenancy

**Team Isolation** (4 weeks)
- Teams can only see their campaigns
- Team-based access control
- Separate EventBridge schedule groups per team
- Team admin role

**Shared Campaigns** (2 weeks)
- Multiple owners per campaign
- Delegated access
- Team collaboration

---

### Advanced Features

**Business Hours Awareness** (2 weeks)
- Only send during business hours (9am-5pm)
- Timezone handling
- Holiday calendar integration
- Weekend skip logic

**Smart Escalation** (3 weeks)
- Adaptive delays based on response rates
- Escalation prediction
- Urgency scoring
- Automatic schedule optimization

**Advanced Reporting** (3-4 weeks)
- Verification rate dashboards
- Campaign performance metrics
- Contact engagement analytics
- Compliance reports
- Data exports (CSV, Excel)

**Audit System** (2 weeks)
- Immutable audit table
- Who accessed what data
- Compliance logging
- Long-term S3 archive
- Audit trail UI

**Template Editor UI** (2-3 weeks)
- Web-based template editor
- Preview with sample data
- Version control
- Template library

**Database-Stored Templates** (1 week)
- Custom templates per campaign
- Template overrides
- Hybrid: defaults in files, overrides in DB

---

## Roadmap Summary

| Phase | Timeline | Key Features | Total Effort |
|-------|----------|--------------|--------------|
| **MVP** | Weeks 1-10 | Core functionality, email, employee directory | 8-10 weeks |
| **MVP+ Quick Wins** | Weeks 11-14 | Hash verification, MySQL, REST API, orphan notifications, simple UI | ~4 weeks |
| **MVP+ Medium** | Weeks 15-24 | Teams/Slack, RBAC, caching, verification portal | ~10 weeks |
| **Future** | TBD | ECS isolation, multi-tenancy, advanced features | Ongoing |

---

## Feature Prioritization Framework

When deciding what to build next, consider:

1. **User Requests** - What are users actively asking for?
2. **Adoption Blockers** - What prevents new teams from onboarding?
3. **Technical Debt** - What will be harder to add later?
4. **Competitive Advantage** - What differentiates ECHO?
5. **Effort vs Value** - What has best ROI?

**Quick Win Criteria:**
- ✅ 1-2 weeks effort
- ✅ Unblocks specific user segment
- ✅ Low risk, high value

**Medium Feature Criteria:**
- ✅ 2-4 weeks effort
- ✅ Significant value add
- ✅ Moderate complexity

**Future/Long-term Criteria:**
- ✅ 4+ weeks effort
- ✅ Requires significant refactoring
- ✅ Enterprise-scale features

---

## Versioning Strategy

**Semantic Versioning:**
- **v1.0.0** - MVP launch (first production deployment)
- **v1.1.0** - Minor features (quick wins)
- **v1.2.0** - Minor features (continued)
- **v2.0.0** - Major features (medium features, breaking changes if needed)

**Release Cadence:**
- MVP: One large release
- Post-MVP: 2-week sprints
- Quick wins: 1-2 per sprint
- Medium features: 2-4 sprints each

---

## Success Metrics

**MVP Success:**
- 3+ production campaigns running
- 50+ notifications sent
- 95%+ delivery success rate
- Manager escalations working
- Zero critical bugs

**MVP+ Success:**
- 10+ production campaigns
- 5+ different teams using ECHO
- 1000+ notifications sent
- Multiple data source types in use
- Positive user feedback

**Long-term Success:**
- 50+ production campaigns
- 20+ teams using ECHO
- 10,000+ notifications/month
- Multi-tenancy in use
- Self-service onboarding

---

## Open Questions for Roadmap

1. **Which quick win first?** Hash verification or MySQL support?
2. **When to add UI?** Before or after Teams/Slack channels?
3. **RBAC timing?** Essential for MVP+ or can wait?
4. **Verification Portal Kit?** Build in-house or let teams customize?
5. **Multi-tenancy priority?** When do we actually need it?

**Answers driven by:**
- User feedback from MVP
- Adoption patterns
- Resource constraints
- Strategic priorities

---

**Next Step:** Complete MVP (8-10 weeks), gather feedback, prioritize MVP+ features based on actual usage.
