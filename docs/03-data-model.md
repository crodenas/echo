# Data Model

This document defines the data structures, schemas, and requirements for ECHO.

## Data Source Requirements

### Required Fields

Every data source must provide these minimum fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `object_id` | String | Unique identifier for the record | `"service-123"`, `"db-prod-456"` |
| `contact_1` | String | Primary contact system ID | `"alice@example.com"` |

### Recommended Fields

These fields significantly improve ECHO's effectiveness:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `last_updated` | Timestamp | When record was last modified | `"2024-01-15T10:30:00Z"` |
| `last_verified` | Timestamp | When record was last confirmed | `"2024-01-10T14:00:00Z"` |
| `contact_2`, `contact_3`, ... | String | Additional contacts | `"bob@example.com"` |
| `name` | String | Display name for the resource | `"Payment Processing API"` |
| `description` | String | Brief description | `"Handles credit card transactions"` |
| `url` | String | Link to resource details | `"https://portal.example.com/services/123"` |
| `owner_team` | String | Owning team name | `"payments"` |

### Optional Metadata

Any additional fields can be included and used in notification templates:
- `environment` (production, staging, dev)
- `criticality` (high, medium, low)
- `technology` (Java, Python, Node.js)
- `cost_center`, `department`, etc.

### Data Source Examples

**SQL View:**
```sql
CREATE VIEW echo_services_view AS
SELECT
  service_id AS object_id,
  service_name AS name,
  description,
  primary_contact AS contact_1,
  secondary_contact AS contact_2,
  last_updated_date AS last_updated,
  last_verified_date AS last_verified,
  portal_url AS url,
  owner_team,
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
      "contact_1": "alice@example.com",
      "contact_2": "bob@example.com",
      "last_updated": "2024-01-15T10:30:00Z",
      "last_verified": "2024-01-10T14:00:00Z",
      "url": "https://portal.example.com/services/123",
      "metadata": {
        "owner_team": "payments",
        "environment": "production",
        "criticality": "high"
      }
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
  data_source_config JSONB NOT NULL,      -- Connection details

  -- Scheduling
  campaign_schedule VARCHAR(100) NOT NULL,  -- AWS cron expression
  cycle_schedule VARCHAR(100) NOT NULL,     -- AWS cron expression
  escalation_count INTEGER NOT NULL,

  -- Escalation rules
  escalation_rules JSONB NOT NULL,

  -- Notification configuration
  notification_templates JSONB NOT NULL,
  notification_channels VARCHAR[] NOT NULL,  -- ['email', 'teams', 'slack']

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
  "campaign_schedule": "cron(0 0 1 */3 ? *)",
  "cycle_schedule": "cron(0 12 * * ? *)",
  "escalation_count": 3,
  "escalation_rules": [
    {"level": 1, "recipients": ["record_contacts"], "delay_days": 0},
    {"level": 2, "recipients": ["record_contacts"], "delay_days": 7},
    {"level": 3, "recipients": ["record_contacts", "team_lead@example.com"], "delay_days": 14}
  ],
  "notification_templates": {
    "email": "default_email_template",
    "teams": "default_teams_template"
  },
  "notification_channels": ["email", "teams"],
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
  current_escalation_level INTEGER DEFAULT 1,

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

### Record Table

```sql
CREATE TABLE records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cycle_id UUID NOT NULL REFERENCES cycles(id) ON DELETE CASCADE,
  campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,

  -- Source data
  object_id VARCHAR(255) NOT NULL,
  source_data JSONB NOT NULL,  -- Full record from data source

  -- Contacts
  contacts VARCHAR[] NOT NULL,  -- Array of system IDs

  -- Verification tracking
  verification_status VARCHAR(50) NOT NULL,  -- 'verified', 'unverified', 'stale'
  last_updated TIMESTAMP,
  last_verified TIMESTAMP,
  verified_in_cycle BOOLEAN DEFAULT false,

  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_records_cycle ON records(cycle_id);
CREATE INDEX idx_records_campaign ON records(campaign_id);
CREATE INDEX idx_records_object ON records(object_id);
CREATE INDEX idx_records_status ON records(verification_status);
```

**Example Row:**
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440001",
  "cycle_id": "750e8400-e29b-41d4-a716-446655440002",
  "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
  "object_id": "service-123",
  "source_data": {
    "name": "Payment Processing API",
    "description": "Handles credit card transactions",
    "url": "https://portal.example.com/services/123",
    "owner_team": "payments",
    "environment": "production"
  },
  "contacts": ["alice@example.com", "bob@example.com"],
  "verification_status": "unverified",
  "last_updated": "2024-01-15T10:30:00Z",
  "last_verified": "2024-01-10T14:00:00Z",
  "verified_in_cycle": false
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

  -- Records included
  record_ids UUID[] NOT NULL,
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
   │                    │
   └─────< (N) Record <─┘
              │
              │
           (N) Notification (grouped by recipient)
```

## Change Detection Strategies

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
def calculate_hash(record):
    """Calculate hash of critical fields."""
    fields = [
        record.name,
        record.description,
        ','.join(sorted(record.contacts))
    ]
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

If contacts changed, consider it verified (someone updated it):

```python
def contacts_changed(old_record, new_record):
    """Check if contacts were modified."""
    return set(old_record.contacts) != set(new_record.contacts)
```

## Notification Templates

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
      "url": "https://portal.example.com/services/123",
      "last_verified": "2024-01-10",
      "metadata": { ... }
    }
  ],
  "record_count": 5
}
```

### Email Template Example

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
        <td><a href="{{ record.url }}">Verify</a></td>
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
