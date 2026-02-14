# Workflows

This document describes the operational workflows and processes in ECHO.

## Campaign Lifecycle

### 1. Campaign Creation

**User Actions:**
1. Access ECHO admin interface
2. Click "Create Campaign"
3. Configure campaign parameters:
   - Name and description
   - Data source connection (SQL/API/HTTP)
   - Campaign schedule (how often to start cycles)
   - Cycle schedule (notification frequency)
   - Escalation count and rules
   - Notification templates and channels

**System Actions:**
1. Validate configuration
2. Test data source connection
3. Create campaign record in database
4. Create AWS EventBridge schedule group
5. Create campaign schedule in EventBridge
6. Set campaign status to "enabled"

**Validation Checks:**
- Data source connection is valid
- Required fields are present in data source
- Campaign frequency > cycle duration
- Escalation rules are well-formed
- Templates exist for selected channels

### 2. Campaign Execution (Ongoing)

**Automatic Process:**
1. EventBridge triggers campaign schedule
2. ECHO creates new cycle instance
3. Cycle executes (see "Wave Execution" below)
4. Repeat on schedule indefinitely

**Monitoring:**
- Dashboard shows active cycles per campaign
- Metrics track verification rates
- Alerts on campaign failures

### 3. Campaign Modification

**User Actions:**
1. Update campaign settings
2. Modify schedules, escalation rules, or templates

**System Actions:**
1. Validate changes
2. Update campaign record
3. Update EventBridge schedules if schedule changed
4. Apply changes to future cycles (not in-progress cycles)

**Important:** Changes don't affect currently running cycles.

### 4. Campaign Pause/Resume

**Pause:**
1. Set campaign to disabled
2. Disable EventBridge schedule
3. Allow current cycle to complete
4. Don't start new cycles

**Resume:**
1. Set campaign to enabled
2. Re-enable EventBridge schedule
3. New cycle starts on next scheduled time

### 5. Campaign Deletion

**User Actions:**
1. Request campaign deletion
2. Confirm action (permanent)

**System Actions:**
1. Disable campaign immediately
2. Cancel in-progress cycles (optional)
3. Delete EventBridge schedule group
4. Archive campaign data
5. Delete campaign record (or mark as deleted)

## Wave Execution Workflow

### Phase 1: Initialization

```
Campaign Schedule Triggers
  └─> Create Cycle Record
      ├─> cycle_id = new UUID
      ├─> campaign_id = reference
      ├─> start_date = now
      ├─> status = 'in_progress'
      └─> current_escalation_level = 1
```

### Phase 2: Data Ingestion

```
1. CONNECT to data source
   ├─> SQL: Execute query
   ├─> API: Call endpoint
   └─> HTTP: Fetch URL

2. FETCH current records
   └─> Parse response (JSON/CSV)

3. VALIDATE records
   ├─> Check required fields present
   └─> Validate data types

4. TRANSFORM records
   └─> Map to ECHO record format

5. LOAD into database
   ├─> Create record entries
   ├─> Link to cycle_id
   ├─> Set initial status = 'unverified'
   └─> Update cycle.total_records
```

**Error Handling:**
- Connection failures: Retry with exponential backoff
- Invalid data: Skip record, log warning
- Missing required fields: Skip record, log error
- Complete failure: Cancel cycle, alert admin and campaign owner

### Phase 3: Verification Assessment

```
FOR EACH record in cycle:
  1. CHECK verification status
     ├─> Has last_verified timestamp?
     ├─> Is last_verified >= cycle.start_date?
     └─> Are any contact fields changed since last sync?

  2. APPLY verification logic
     └─> If verified: set status = 'verified'
     └─> Else: set status = 'unverified'

  3. UPDATE cycle statistics
     ├─> verified_records count
     └─> unverified_records count
```

### Phase 4: Notification Generation

```
1. FILTER unverified records
   └─> WHERE status = 'unverified'

2. GROUP by contact
   └─> Each contact gets one notification with all their records

3. APPLY escalation rules
   ├─> Determine recipients for current level
   └─> Add static recipients if configured

4. BUILD notifications
   FOR EACH recipient:
     ├─> Get records assigned to recipient
     ├─> Render template with record data
     ├─> Create notification record
     └─> Set status = 'pending'
```

**Grouping Example:**
```
Records:
  - service-1: owner = alice, system_custodian = bob
  - service-2: owner = alice
  - service-3: owner = charlie

Escalation Level 0 configured with recipients: ["owner"]
Notifications Created:
  - To: alice (records: [service-1, service-2])
  - To: charlie (records: [service-3])

Escalation Level 1 configured with recipients: ["owner", "system_custodian"]
Notifications Created:
  - To: alice (records: [service-1, service-2])
  - To: bob (records: [service-1])
  - To: charlie (records: [service-3])
```

### Phase 5: Notification Delivery

```
FOR EACH notification in queue:
  1. SELECT channel
     └─> Email, Teams, Slack, etc.

  2. PREPARE message
     ├─> Render template
     ├─> Format for channel
     └─> Include record details

  3. SEND notification
     ├─> Call channel API/SMTP
     └─> Handle response

  4. UPDATE status
     ├─> Success: status = 'sent'
     ├─> Failure: status = 'failed', log error
     └─> Set sent_at timestamp

  5. TRACK delivery
     └─> Update notification record
```

**Retry Logic:**
```
IF delivery fails:
  ├─> Increment retry_count
  ├─> IF retry_count < MAX_RETRIES:
  │   └─> Schedule retry (exponential backoff)
  └─> ELSE:
      └─> status = 'failed', alert admin
```

### Phase 6: Escalation Scheduling

```
1. CHECK if more escalations remain
   └─> IF current_level < escalation_count

2. SCHEDULE next escalation
   ├─> Calculate next trigger time
   │   └─> start_date + escalation_rules[level].delay_days
   ├─> Create EventBridge schedule
   └─> Set next_escalation_at

3. WAIT for next escalation trigger

4. ON TRIGGER:
   ├─> Increment current_escalation_level
   └─> REPEAT Phases 2-5
```

### Phase 7: Cycle Completion

```
Cycle completes when:
  - All records verified, OR
  - Max escalations reached

Actions:
  1. SET status = 'completed'
  2. SET end_date = now
  3. SET completed_at = now
  4. CALCULATE final statistics
  5. GENERATE completion report
  6. NOTIFY campaign owner (optional)
```

## Escalation Flow

### Linear Escalation (Default)

```
Level 0: Day 0  → Initial notification to owner
         ↓
        Wait 7 days
         ↓
Level 1: Day 7  → First reminder to owner + system_custodian
         ↓
        Wait 7 days
         ↓
Level 2: Day 14 → Second reminder to owner + system_custodian + owner.manager
         ↓
        Cycle ends
```

### Custom Escalation Example

```json
{
  "escalations": [
    {
      "level": 0,
      "recipients": ["owner"],
      "delay_days": 0,
      "message": "Please verify your resources"
    },
    {
      "level": 1,
      "recipients": ["owner", "system_custodian"],
      "delay_days": 3,
      "message": "Reminder: Verification needed"
    },
    {
      "level": 2,
      "recipients": ["owner", "system_custodian", "owner.manager"],
      "delay_days": 7,
      "message": "Final notice: Escalated to manager"
    },
    {
      "level": 3,
      "recipients": ["team_lead@example.com"],
      "delay_days": 10,
      "message": "Unverified resources require attention"
    }
  ]
}
```

## User Interaction Workflows

### Receiving a Notification

**User Receives:**
- Email/Teams/Slack message
- Subject: "[Campaign Name] - Verification Required"
- Body: List of resources needing verification
- Links to resource details in source system

**User Actions:**
1. Click link to resource portal
2. Review resource information
3. Update metadata if needed
4. Verify/confirm accuracy

**System Detection:**
- Option 1: `last_verified` timestamp updated in source
- Option 2: User clicks "Verify" link (ECHO API)
- Option 3: Metadata changed (detected on next sync)

### Manual Verification (Optional Feature)

If ECHO provides verification endpoints:

**User Clicks "Verify All" Link:**
```
GET /verify?cycle_id={id}&token={auth_token}&contact={email}
  └─> Mark all records for this contact as verified
  └─> Return confirmation page
```

**API Endpoint:**
```http
POST /api/verify
Authorization: Bearer {token}
Content-Type: application/json

{
  "cycle_id": "750e8400-...",
  "object_ids": ["service-123", "service-456"],
  "verified_by": "alice@example.com"
}
```

## Edge Case Workflows

### 1. Record Without Contact Fields

**Scenario:** Data source returns record with no contact fields (or all contact fields are null/empty).

**Workflow:**
```
1. DETECT contact-less record during ingestion
2. LOG warning with object_id
3. SKIP notification for this record
4. ADD to campaign owner's summary report
5. ESCALATE to campaign owner if configured
```

**Configuration Option:**
```json
{
  "orphan_record_policy": {
    "action": "escalate_to_owner",
    "owner_email": "campaign-owner@example.com"
  }
}
```

### 2. Overlapping Cycles

**Scenario:** New cycle starts before previous completes.

**Prevention:**
- Validate campaign_frequency > cycle_duration during creation
- Check for active cycle before starting new one

**If Overlap Occurs:**
```
1. DETECT active cycle exists
2. LOG warning
3. OPTIONS:
   ├─> Skip new cycle (wait for next schedule)
   ├─> Force complete old cycle
   └─> Run in parallel (records in both cycles)
```

### 3. Data Source Failure

**Scenario:** Cannot connect to data source during sync.

**Workflow:**
```
1. ATTEMPT connection
2. ON FAILURE:
   ├─> LOG error with details
   ├─> INCREMENT failure_count
   ├─> RETRY with exponential backoff
   └─> IF all retries fail (complete failure):
       ├─> CANCEL cycle
       ├─> ALERT admin and campaign owner
       └─> SET status = 'cancelled'

3. MANUAL recovery required
   └─> Admin or campaign owner can restart cycle after fixing data source
```

### 4. Mid-Cycle Campaign Update

**Scenario:** User modifies campaign while cycle is running.

**Behavior:**
- In-progress cycles continue with old settings
- New cycles use updated settings
- No retroactive changes to running cycles

### 5. Campaign Disabled Mid-Cycle

**Scenario:** User disables campaign while cycle is in progress.

**Behavior:**
```
1. SET campaign.enabled = false
2. STOP creating new cycles
3. ALLOW in-progress cycles to complete normally
   ├─> Existing escalation jobs continue to execute
   └─> Records can still be verified
4. Campaign schedule remains in scheduler
   └─> When schedule fires, check enabled flag and skip if false
```

**Re-enabling:**
```
1. SET campaign.enabled = true
2. Wait for next scheduled cycle
3. Start fresh cycle (doesn't resume or catch up)
```

**Force Stop (Manual):**
If immediate cancellation needed, manually:
- Delete cycle records from database
- Cancel escalation jobs in scheduler
- Notify affected contacts (optional)

### 6. Stale Verification

**Scenario:** Record hasn't been verified in multiple cycles.

**Detection:**
```sql
SELECT object_id, last_verified
FROM records
WHERE last_verified < NOW() - INTERVAL '90 days'
   OR last_verified IS NULL;
```

**Action:**
```
1. MARK as 'stale' status
2. INCREASE notification priority
3. ESCALATE directly to higher level
4. NOTIFY campaign owner in summary
```

## Reporting Workflows

### Campaign Dashboard

**Metrics Displayed:**
- Active campaigns count
- Current cycles in progress
- Overall verification rate
- Recent notifications sent
- Failed deliveries

### Cycle Report

**Generated on Completion:**
- Total records processed
- Verification rate by escalation level
- Response time metrics
- Contact engagement statistics
- Unverified records list

### Notification Audit Trail

**Queryable Fields:**
- Who was notified
- When notification sent
- Delivery status
- Records included
- Channel used
