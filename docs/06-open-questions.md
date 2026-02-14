# Open Questions & Design Decisions

This document tracks unresolved design questions and decisions that need to be made before implementation.

## Critical Questions

### 1. Verification Detection Method

**Question:** How should ECHO determine if a record has been verified?

**Options:**

**A. Timestamp-based (Simple)**
- Rely on `last_verified` or `last_updated` fields in source data
- ✅ Pros: Simple, no ECHO API needed, leverages existing data
- ❌ Cons: Requires source system to maintain timestamps, may miss nuanced changes

**B. Change Detection (Moderate)**
- Calculate hash of critical fields, detect any changes
- ✅ Pros: Works without timestamps, detects actual updates
- ❌ Cons: May false-positive on trivial changes, requires field selection

**C. Explicit Confirmation (Complex)**
- Provide ECHO API endpoint for explicit "verified" confirmation
- ✅ Pros: Unambiguous, gives users control, tracks who verified
- ❌ Cons: Requires ECHO integration, extra user step beyond portal update

**D. Hybrid Approach (Recommended)**
- Support multiple detection methods per campaign
- Campaign owner chooses: timestamp, change detection, explicit, or combination
- ✅ Pros: Flexible, supports different team workflows
- ❌ Cons: More complex implementation, requires clear documentation

**Recommendation:** Start with **Timestamp-based (A)** for MVP, add **Hybrid (D)** in later iterations.

**Decision:** ✅ **DECIDED - See [decisions.md](decisions.md#decision-1-verification-detection-method)**
- Tiered approach: Tier 0 (hash-based) + Tier 1 (timestamp-based)
- Auto-detect best tier from data source
- Date: 2026-02-14

---

### 2. Contact-less Records Handling

**Question:** What should happen when a record has no valid contacts?

**Options:**

**A. Skip and Retry**
- Don't notify anyone, mark as "orphaned"
- Retry in next cycle, hope contacts are added
- ✅ Pros: Simple, non-disruptive
- ❌ Cons: Record never gets verified, silent failure

**B. Escalate to Campaign Owner**
- Send summary of orphaned records to campaign owner
- Owner can manually address or update source data
- ✅ Pros: Ensures visibility, owner can fix root cause
- ❌ Cons: Manual intervention required

**C. Assign Default Contacts**
- Campaign configuration includes fallback contacts
- Use fallback if record contacts are empty
- ✅ Pros: Ensures notification always happens
- ❌ Cons: May notify wrong people, requires configuration

**D. Combination Approach**
- Mark as orphaned, include in cycle
- Send owner summary report at cycle end
- Allow configuration of fallback contacts
- ✅ Pros: Flexible, provides multiple remediation paths
- ❌ Cons: Most complex to implement

**Recommendation:** **Combination Approach (D)** - log orphans, notify owner in summary, support optional fallback.

**Decision:** ✅ **DECIDED - See [decisions.md](decisions.md#decision-2-contact-less-records-handling)**
- Notify campaign owner at cycle start
- Date: 2026-02-14

---

### 3. Cycle Overlap Management

**Question:** What happens if a new campaign cycle starts before the previous one completes?

**Context:** Campaign frequency might be set too short, or escalations might take longer than expected.

**Options:**

**A. Prevent Overlap (Strict)**
- Check for active cycle before starting new one
- Skip new cycle if previous is still active
- ✅ Pros: Simple, avoids confusion, prevents duplicate notifications
- ❌ Cons: Might miss a scheduled cycle, requires monitoring

**B. Force Complete Previous (Aggressive)**
- Auto-complete the old cycle when new one starts
- Mark remaining unverified records as "skipped"
- ✅ Pros: Ensures new cycle starts on time
- ❌ Cons: Loses data, may prematurely end legitimate verification process

**C. Allow Parallel Cycles (Complex)**
- Run both cycles simultaneously
- Records can be in multiple active cycles
- ✅ Pros: Doesn't lose cycles, maximum pressure for verification
- ❌ Cons: Complex logic, duplicate notifications, user confusion

**D. Validation + Skip (Recommended)**
- Validate during campaign creation: `campaign_frequency > estimated_cycle_duration`
- At runtime: Skip new cycle if overlap detected, log warning
- Alert campaign owner to adjust schedule
- ✅ Pros: Prevents issue, provides clear feedback, simple runtime logic
- ❌ Cons: Requires good duration estimation

**Recommendation:** **Validation + Skip (D)** - prevent at creation, skip with alert at runtime.

**Decision:** ✅ **DECIDED - See [decisions.md](decisions.md#decision-3-cycle-overlap-management)**
- Two-layer protection: Validation + Skip
- Date: 2026-02-14

---

### 4. Multi-Channel Notification Strategy

**Question:** If multiple channels are configured (email + Teams + Slack), how should they be used?

**Options:**

**A. Send to All Channels**
- Every notification goes to all configured channels
- User gets email AND Teams AND Slack message
- ✅ Pros: Maximum reach, user chooses their preference
- ❌ Cons: Notification fatigue, redundant messages

**B. Channel Priority/Fallback**
- Try primary channel, fallback if failure
- Example: Try Teams, fallback to email if user not in Teams
- ✅ Pros: Reduces duplication, smart delivery
- ❌ Cons: Complex logic, requires channel health checking

**C. User Preference**
- Each user configures their preferred channel
- ECHO sends only to preferred channel
- ✅ Pros: Respects user choice, reduces noise
- ❌ Cons: Requires user management, what if preference not set?

**D. Campaign-Level Choice**
- Campaign owner selects ONE channel per campaign
- All notifications for that campaign use that channel
- ✅ Pros: Simple, consistent per campaign
- ❌ Cons: Doesn't respect individual preferences

**Recommendation:** Start with **Campaign-Level Choice (D)** for MVP, add **User Preference (C)** later.

**Decision:** ✅ **DECIDED - See [decisions.md](decisions.md#decision-4-multi-channel-notification-strategy)**
- Campaign-level, email-only for MVP, extensible architecture
- Date: 2026-02-14

---

### 5. Notification Frequency Within Cycle

**Question:** How often should notifications be sent during a cycle?

**Options:**

**A. Fixed Schedule**
- Campaign defines: "Send every 7 days"
- Escalations trigger at fixed intervals
- ✅ Pros: Predictable, easy to configure
- ❌ Cons: Inflexible, may not suit all workflows

**B. Smart Escalation**
- Longer delays between early escalations
- Shorter delays as cycle nears end (urgency increases)
- ✅ Pros: Natural escalation curve, respects user time early
- ❌ Cons: Complex to configure, less predictable

**C. Business Hours Awareness**
- Only send during business hours (9am-5pm, Mon-Fri)
- Respect time zones
- ✅ Pros: Professional, respects work-life balance
- ❌ Cons: Complex timezone handling, delays delivery

**D. Configurable Per Escalation**
- Each escalation level has its own delay
- Campaign owner has full control
- ✅ Pros: Maximum flexibility, supports any pattern
- ❌ Cons: Requires more configuration effort

**Recommendation:** **Configurable Per Escalation (D)** with suggested templates for common patterns.

**Decision:** ✅ **DECIDED - See [decisions.md](decisions.md#decision-5-notification-frequency-within-cycle)**
- Configurable per escalation (simple approach)
- Date: 2026-02-14

---

## Implementation Questions

### 6. Scheduler Technology Choice

**Question:** APScheduler (in-process) or AWS EventBridge (external)?

**APScheduler:**
- ✅ Simple deployment, no external dependencies
- ✅ Good for development and single-instance
- ❌ Doesn't scale horizontally, lost if instance crashes
- ❌ No persistence across restarts

**AWS EventBridge:**
- ✅ Distributed, highly available
- ✅ Persistent schedules, survives restarts
- ✅ Scales with load
- ❌ AWS-specific, vendor lock-in
- ❌ More complex setup and testing

**Recommendation:** Use **both** - APScheduler for development/local, EventBridge for production. Abstract behind scheduler interface.

**Decision:** ✅ **DECIDED - See [decisions.md](decisions.md#decision-6-scheduler-technology-choice)**
- EventBridge for all environments with schedule groups (no APScheduler)
- Date: 2026-02-14

---

### 7. Database Choice

**Question:** Which database technology?

**Options:**

**A. PostgreSQL**
- ✅ Rich SQL features, JSONB support
- ✅ Excellent for relational + semi-structured data
- ✅ Strong consistency, ACID transactions
- ❌ Vertical scaling limits (though very high)

**B. MongoDB**
- ✅ Flexible schema, native JSON
- ✅ Horizontal scaling
- ❌ Weaker consistency guarantees
- ❌ Less suitable for relational data

**C. DynamoDB**
- ✅ Fully managed, AWS native
- ✅ Infinite scale, low ops overhead
- ❌ Complex query patterns, limited flexibility
- ❌ Cost can be high

**Recommendation:** **PostgreSQL** - good fit for relational data model, JSONB handles flexible metadata, proven technology.

**Decision:** ✅ **DECIDED - See [decisions.md](decisions.md#decision-7-database-choice)**
- PostgreSQL with connection string configuration
- Date: 2026-02-14

---

### 8. Template System

**Question:** How should notification templates be managed?

**Options:**

**A. Jinja2 Templates in Files**
- Store templates as `.html`/`.txt` files
- Load from filesystem
- ✅ Pros: Easy to edit, version control friendly
- ❌ Cons: Requires deployment for changes

**B. Database-Stored Templates**
- Store templates in database
- Edit via admin UI
- ✅ Pros: No deployment needed, user-editable
- ❌ Cons: No version control, harder to backup

**C. Hybrid Approach**
- Default templates in files
- Custom templates in database (override defaults)
- ✅ Pros: Best of both worlds
- ❌ Cons: More complex implementation

**Recommendation:** **Hybrid Approach (C)** - ship good defaults, allow customization.

**Decision:** ✅ **DECIDED - See [decisions.md](decisions.md#decision-8-template-system)**
- Jinja2 templates in files for MVP
- Date: 2026-02-14

---

## Feature Scope Questions

### 9. Campaign Modes (SVT, AVT, CVT)

**Question:** Should we implement different campaign "modes" or keep one flexible model?

**Background:** Early docs mentioned:
- **SVT**: Standard verification (regular intervals)
- **AVT**: Automated verification (time-based triggers)
- **CVT**: Contact validation (watch for missing contacts)

**Options:**

**A. Separate Modes**
- Different campaign types with mode-specific features
- Clearer UX, targeted for use case
- ❌ Cons: More code, less flexible

**B. Unified Flexible Model**
- Single campaign type, configuration handles differences
- SVT = regular schedule
- AVT = calendar-based schedule
- CVT = filter for missing contacts + special escalation
- ✅ Pros: Simpler codebase, more flexible
- ❌ Cons: May be harder to configure for specific use cases

**Recommendation:** **Unified Flexible Model (B)** - one campaign type, use cases emerge from configuration.

**Decision:** ✅ **DECIDED - See [decisions.md](decisions.md#decision-9-campaign-modes-svt-avt-cvt)**
- Unified flexible model (single campaign type)
- Date: 2026-02-14

---

### 10. User Management

**Question:** Does ECHO need its own user authentication system?

**Options:**

**A. No User Management (Simplest)**
- API keys for programmatic access
- No login, no user accounts
- ✅ Pros: Minimal implementation, focus on core features
- ❌ Cons: No multi-tenancy, no role-based access

**B. Basic Authentication**
- Simple login system
- User roles: admin, campaign owner, viewer
- ✅ Pros: Enables multi-tenancy, access control
- ❌ Cons: Requires user management, password handling

**C. SSO Integration**
- Integrate with corporate SSO (SAML, OAuth)
- No password management
- ✅ Pros: Enterprise-friendly, leverages existing auth
- ❌ Cons: Complex integration, environment-specific

**Recommendation:** Start with **API Keys (A)** for MVP, add **SSO (C)** when multi-tenancy is needed.

**Decision:** ✅ **DECIDED - See [decisions.md](decisions.md#decision-10-user-management)**
- No user management for MVP (owner_email field only)
- Date: 2026-02-14

---

### 11. Audit and Compliance

**Question:** What level of audit logging is needed?

**Considerations:**
- Who created/modified campaigns?
- Who was notified and when?
- What data was accessed from sources?
- Who verified what records?

**Recommendation:** Comprehensive audit logging from day one:
- All campaign CRUD operations
- All notification sends
- All verification actions
- Data source access logs

Immutable audit table, never delete, archive to S3 for long-term retention.

**Decision:** ✅ **DECIDED - See [decisions.md](decisions.md#decision-11-audit-and-compliance)**
- Standard Python logging for MVP
- Date: 2026-02-14

---

## Next Steps

### Decision Process

For each open question:
1. Review options and recommendations
2. Consider MVP vs. future features
3. Validate assumptions with stakeholders
4. Document final decision
5. Update design docs accordingly

### Priority for MVP

**Must Decide Before Implementation:**
- [x] Verification detection method (#1) ✅ **DECIDED**
- [x] Contact-less records handling (#2) ✅ **DECIDED**
- [x] Cycle overlap management (#3) ✅ **DECIDED**
- [x] Notification channel strategy (#4) ✅ **DECIDED**
- [x] Scheduler choice (#6) ✅ **DECIDED**
- [x] Database choice (#7) ✅ **DECIDED**

**Decided for MVP (Simple Approaches):**
- [x] Business hours awareness (#5) ✅ **DECIDED** - Deferred to post-MVP
- [x] Campaign modes (#9) ✅ **DECIDED** - Unified model
- [x] User management approach (#10) ✅ **DECIDED** - No auth for MVP
- [x] Template system details (#8) ✅ **DECIDED** - Files for MVP
- [x] Audit requirements (#11) ✅ **DECIDED** - Python logging for MVP

**All decisions finalized. See [decisions.md](decisions.md) for complete details.**

### Decision Template

When making a decision, document it like this:

```markdown
## Decision: [Question Number] - [Title]

**Date:** YYYY-MM-DD
**Decided By:** [Name/Team]

**Selected Option:** [A/B/C/D]

**Rationale:**
- [Why this option was chosen]
- [What trade-offs were accepted]
- [What assumptions were made]

**Implications:**
- [Impact on architecture]
- [Impact on implementation timeline]
- [Impact on user experience]

**Revisit Criteria:**
- [When/why we might reconsider this decision]
```
