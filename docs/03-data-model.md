# Data Model

This document defines the data structures, schemas, and requirements for ECHO.

## Data Source Requirements

### Required Fields

Every data source must provide these minimum fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `object_id` | String | Unique identifier for the record | `"service-123"`, `"db-prod-456"` |
| (at least one contact field) | String | Contact identifier named by source system | `"owner": "alice@example.com"` |

**Note:** Contact field names are defined by the source system based on organizational terminology (e.g., `owner`, `system_custodian`, `primary_it_contact`, `service_owner`, etc.). Each contact field contains a single contact identifier.

### Recommended Fields

These fields significantly improve ECHO's effectiveness:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `last_updated` | Timestamp | When record was last modified | `"2024-01-15T10:30:00Z"` |
| `last_verified` | Timestamp | When record was last confirmed | `"2024-01-10T14:00:00Z"` |
| Additional contact fields | String | Additional role-based contacts | `"backup_owner": "bob@example.com"` |
| `name` | String | Display name for the resource | `"Payment Processing API"` |
| `description` | String | Brief description | `"Handles credit card transactions"` |

### Additional Fields

Any additional fields from the data source are passed through to notification templates. ECHO does not require or define specific optional fields - include whatever is useful for your templates.

**Examples:** `environment`, `criticality`, `technology`, `cost_center`, `department`, etc.

### Data Source Examples

**SQL View:**
```sql
CREATE VIEW echo_services_view AS
SELECT
  service_id AS object_id,
  service_name AS name,
  description,
  service_owner AS owner,
  system_custodian,
  backup_contact,
  last_updated_date AS last_updated,
  last_verified_date AS last_verified,
  environment,
  criticality
FROM services
WHERE active = true;
```

**REST API Response:**
```json
{
  "records": [
    {
      "object_id": "service-123",
      "name": "Payment Processing API",
      "description": "Handles credit card transactions",
      "owner": "alice@example.com",
      "system_custodian": "bob@example.com",
      "last_updated": "2024-01-15T10:30:00Z",
      "last_verified": "2024-01-10T14:00:00Z",
      "environment": "production",
      "criticality": "high"
    }
  ]
}
```

## ECHO Database Schema

### Campaign Table

```sql
CREATE TABLE campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,

  -- Data source configuration
  data_source_type VARCHAR(50) NOT NULL,  -- 'sql', 'api', 'http'
  data_source_config JSONB NOT NULL,      -- Connection details and credentials reference
  -- Format: {"host": "...", "database": "...", "query": "...", "credentials_ref": "arn:aws:ssm:..."}
  -- See Decision #17 for credentials storage strategy

  -- Scheduling
  campaign_schedule VARCHAR(100) NOT NULL,  -- AWS cron expression (when to start cycles)
  -- MVP: Raw AWS cron format with validation and presets in UI
  -- UI provides common presets: Monthly, Quarterly, Semi-Annually, Annually
  -- Advanced users can use custom cron syntax
  escalation_rules JSONB NOT NULL,          -- Array of {level, delay_days, recipients} (escalations within cycle)

  -- Record filtering (determines which records need action at each cycle)
  record_filter JSONB NOT NULL DEFAULT '{
    "filter_type": "time_based",
    "config": {"timestamp_field": "last_verified"}
  }',
  -- Filter types: time_based, contact_validity, change_detection, composite
  -- See docs/07-record-filters.md for complete specification

  -- Notification configuration
  notification_templates JSONB NOT NULL,
  -- Format: {"email": "template_name", "teams": "template_name", "slack": "template_name"}
  -- Email template is REQUIRED, others are optional
  -- Channels are enabled if: (1) template exists AND (2) delivery mechanism configured
  -- MVP: Email only (teams/slack deferred to MVP+)
  notification_channels VARCHAR[] NOT NULL,  -- ['email', 'teams', 'slack'] - enabled channels

  -- Status
  enabled BOOLEAN DEFAULT true,
  last_run_at TIMESTAMP,

  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255),
  owner_team VARCHAR(255)
);
```

**Example Row:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Q1 Service Verification",
  "description": "Quarterly verification of all production services",
  "data_source_type": "sql",
  "data_source_config": {
    "connection_string": "postgresql://...",
    "query": "SELECT * FROM echo_services_view"
  },
  "campaign_schedule": "cron(0 0 1 */3 ? *)",  // Start new cycle every 3 months
  "record_filter": {
    "filter_type": "time_based",
    "config": {
      "timestamp_field": "last_verified",
      "comparison": "before_cycle_start"
    }
  },
  "escalation_rules": [                         // Escalations within each cycle
    {"level": 0, "recipients": ["owner"], "delay_days": 0},
    {"level": 1, "recipients": ["owner", "system_custodian"], "delay_days": 7},
    {"level": 2, "recipients": ["owner", "system_custodian", "owner.manager"], "delay_days": 14}
  ],
  "notification_templates": {
    "email": "default_email_template",
    "teams": "default_teams_template"
  },
  "notification_channels": ["email", "teams"],
  "enabled": true
}
```

**Example Campaign with Contact Validity Filter:**
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440001",
  "name": "Invalid Contact Remediation",
  "description": "Weekly notification for services with invalid contacts",
  "data_source_type": "sql",
  "data_source_config": {
    "connection_string": "postgresql://...",
    "query": "SELECT s.*, (s.owner IN (SELECT email FROM employee_directory)) AS owner_is_valid FROM services s"
  },
  "campaign_schedule": "cron(0 9 * * MON *)",  // Every Monday at 9am
  "record_filter": {
    "filter_type": "contact_validity",
    "config": {
      "contact_fields": ["owner", "system_custodian"],
      "validation_source": {
        "type": "data_source_provided",
        "field_name_pattern": "{field}_is_valid"
      }
    }
  },
  "escalation_rules": [
    {"level": 0, "recipients": ["owner"], "delay_days": 0},
    {"level": 1, "recipients": ["owner", "owner.manager"], "delay_days": 3}
  ],
  "notification_templates": {
    "email": "invalid_contact_email_template"
  },
  "notification_channels": ["email"],
  "enabled": true
}
```

### Cycle Table

```sql
CREATE TABLE cycles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,

  -- Timing
  start_date TIMESTAMP NOT NULL,
  end_date TIMESTAMP,
  current_escalation_level INTEGER DEFAULT 0,

  -- Tier 0 verification cache (hash-based, optional)
  record_hashes JSONB,  -- {"object_id": "hash", ...} - Only for Tier 0, NULL for Tier 1

  -- Status
  status VARCHAR(50) NOT NULL,  -- 'in_progress', 'completed', 'cancelled'

  -- Statistics
  total_records INTEGER,
  verified_records INTEGER,
  unverified_records INTEGER,

  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP
);

CREATE INDEX idx_cycles_campaign ON cycles(campaign_id);
CREATE INDEX idx_cycles_status ON cycles(status);
```

**Note:** `record_hashes` is only populated for Tier 0 (hash-based) verification when data source lacks timestamps. For Tier 1 (timestamp-based) verification, this field remains NULL.

**Example Cycle Row:**
```json
{
  "id": "750e8400-e29b-41d4-a716-446655440002",
  "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-14T23:59:59Z",
  "current_escalation_level": 1,
  "record_hashes": {
    "service-123": "a3f5e9d...",
    "service-456": "b8c2f1a...",
    "service-789": "c9d4e2b..."
  },
  "status": "in_progress",
  "total_records": 3,
  "verified_records": 0,
  "unverified_records": 3,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Notification Table

```sql
CREATE TABLE notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cycle_id UUID NOT NULL REFERENCES cycles(id) ON DELETE CASCADE,
  campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,

  -- Recipient
  recipient VARCHAR(255) NOT NULL,

  -- Notification details
  escalation_level INTEGER NOT NULL,
  channel VARCHAR(50) NOT NULL,  -- 'email', 'teams', 'slack'

  -- Content
  subject VARCHAR(500),
  body TEXT,
  template_used VARCHAR(255),

  -- Records included (from data source)
  object_ids VARCHAR(255)[] NOT NULL,  -- Array of object_id values from data source
  record_count INTEGER NOT NULL,

  -- Delivery tracking
  status VARCHAR(50) NOT NULL,  -- 'pending', 'sent', 'delivered', 'failed'
  sent_at TIMESTAMP,
  delivered_at TIMESTAMP,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,

  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_cycle ON notifications(cycle_id);
CREATE INDEX idx_notifications_recipient ON notifications(recipient);
CREATE INDEX idx_notifications_status ON notifications(status);
```

## Data Relationships

```
Campaign (1) ──────< (N) Cycle
   │                    │
   │                    └──< (N) Notification (grouped by recipient)
   │
   └──> Data Source (external, fresh lookup at each escalation)

Notes:
- No records table - records are fetched fresh from data source at each escalation
- Cycle.record_hashes (JSONB) stores hashes for Tier 0 verification only
- Notifications reference object_ids but don't store full record data
```

## Change Detection Strategies

**Note**: These strategies are implemented through the `record_filter` configuration. See [Record Filters](07-record-filters.md) for complete specification and configuration examples.

### 1. Timestamp-Based Detection

Compare `last_verified` or `last_updated` timestamps:

```python
def is_verified(record, cycle_start):
    """Check if record was verified since cycle started."""
    if record.last_verified and record.last_verified >= cycle_start:
        return True
    return False
```

### 2. Change Hash Detection

Calculate hash of critical fields:

```python
def calculate_hash(record, contact_fields):
    """Calculate hash of critical fields including all contact fields."""
    fields = [
        record.name,
        record.description,
    ]
    # Add all contact field values in sorted order
    for field_name in sorted(contact_fields):
        fields.append(f"{field_name}:{record.get(field_name, '')}")
    return hashlib.sha256('|'.join(fields).encode()).hexdigest()
```

### 3. Explicit Confirmation

Provide API endpoint for users to confirm verification:

```http
POST /api/verify
{
  "cycle_id": "...",
  "object_id": "service-123",
  "verified_by": "alice@example.com"
}
```

### 4. Contact Change Detection

If any contact field changed, consider it verified (someone updated it):

```python
def contacts_changed(old_record, new_record, contact_fields):
    """Check if any contact fields were modified."""
    for field_name in contact_fields:
        old_value = old_record.get(field_name)
        new_value = new_record.get(field_name)
        if old_value != new_value:
            return True
    return False
```

## Notification Templates

### Template Structure

Each notification channel (email, Teams, Slack) references a Jinja2 template by ID:

```json
{
  "notification_templates": {
    "email": "service_verification_email",
    "teams": "service_verification_teams",
    "slack": "service_verification_slack"
  }
}
```

**URL Handling:**
URLs are embedded directly in the template content using Jinja2 syntax. This gives template authors full control over URL formatting:

```html
<!-- Email template example -->
<a href="https://portal.example.com/services/{{ record.object_id }}">Verify</a>

<!-- Or with channel tracking -->
<a href="https://portal.example.com/services/{{ record.object_id }}?channel=email&cycle={{ cycle.id }}">Verify</a>
```

### Template Variables

Available in all templates:

```python
{
  "recipient": {
    "name": "Alice Smith",
    "email": "alice@example.com"
  },
  "campaign": {
    "name": "Q1 Service Verification",
    "description": "Quarterly verification..."
  },
  "cycle": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "escalation_level": 1,
  "records": [
    {
      "object_id": "service-123",
      "name": "Payment Processing API",
      "last_verified": "2024-01-10",
      "metadata": { ... }
    }
  ],
  "record_count": 5
}
```

### Email Template Examples

**Template design is flexible** - campaign owners choose how to display records based on their use case.

**Example 1: Inline List (good for small lists)**
```html
<!DOCTYPE html>
<html>
<head>
  <title>{{ campaign.name }} - Verification Required</title>
</head>
<body>
  <h1>{{ campaign.name }}</h1>
  <p>Hi {{ recipient.name }},</p>

  <p>Please verify the following {{ record_count }} resource(s):</p>

  <table>
    <thead>
      <tr>
        <th>Resource</th>
        <th>Last Verified</th>
        <th>Action</th>
      </tr>
    </thead>
    <tbody>
      {% for record in records %}
      <tr>
        <td>{{ record.name }}</td>
        <td>{{ record.last_verified or 'Never' }}</td>
        <td><a href="https://portal.example.com/services/{{ record.object_id }}">Verify</a></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  {% if escalation_level > 1 %}
  <p><strong>Reminder:</strong> This is escalation level {{ escalation_level }}.</p>
  {% endif %}
</body>
</html>
```

**Example 2: Summary + Link (good for large lists)**
```html
<!DOCTYPE html>
<html>
<head>
  <title>{{ campaign.name }} - Verification Required</title>
</head>
<body>
  <h1>{{ campaign.name }}</h1>
  <p>Hi {{ recipient.name }},</p>

  <p>You have <strong>{{ record_count }}</strong> item(s) requiring verification.</p>

  <p><a href="https://portal.example.com/verify?contact={{ recipient.email }}&cycle={{ cycle.id }}"
     style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none;">
    View and Verify All Items
  </a></p>

  {% if escalation_level > 1 %}
  <p><strong>Reminder:</strong> This is escalation level {{ escalation_level }}.</p>
  {% endif %}
</body>
</html>
```

**Note:** The summary + link approach works well when record counts can be large. Campaign owners can point to their source system's portal or ECHO's simple verification page.

## Storage Considerations

### Data Retention

- **Active Cycles**: Keep indefinitely while in progress
- **Completed Cycles**: Retain for 90 days, then archive
- **Notifications**: Retain for audit (1 year minimum)
- **Records**: Current cycle only, historical in cycles

### Partitioning Strategy

Partition large tables by date for performance:

```sql
-- Partition cycles by created_at (monthly)
CREATE TABLE cycles_2024_01 PARTITION OF cycles
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Partition notifications by created_at (weekly)
CREATE TABLE notifications_2024_w01 PARTITION OF notifications
  FOR VALUES FROM ('2024-01-01') TO ('2024-01-08');
```

### Archival Process

Move old data to archive tables or S3:

```sql
-- Archive completed cycles older than 90 days
INSERT INTO cycles_archive
SELECT * FROM cycles
WHERE status = 'completed'
  AND completed_at < NOW() - INTERVAL '90 days';

DELETE FROM cycles
WHERE status = 'completed'
  AND completed_at < NOW() - INTERVAL '90 days';
```
