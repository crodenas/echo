# System Architecture

This document describes ECHO's architectural design, components, and integration patterns.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        ECHO System                          │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐ │
│  │   Input     │───>│  Processing  │───>│    Output     │ │
│  │   Layer     │    │    Engine    │    │    Layer      │ │
│  └─────────────┘    └──────────────┘    └───────────────┘ │
│         │                   │                     │         │
│         v                   v                     v         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              ECHO State Database                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                                            │
         v                                            v
┌──────────────────┐                        ┌──────────────────┐
│  External Data   │                        │   Notification   │
│    Sources       │                        │    Channels      │
│  (Read-Only)     │                        │  (Email, Teams)  │
└──────────────────┘                        └──────────────────┘
```

## Core Components

### 1. Input Layer (Data Ingestion)

**Purpose**: Synchronize external inventory data into ECHO's database.

**Responsibilities:**
- Connect to configured data sources (SQL, API, HTTP)
- Execute queries or API calls to fetch current data
- Transform and validate incoming data
- Detect changes from previous sync
- Update ECHO's internal record cache

**Key Operations:**
- Scheduled data refresh (per cycle or on-demand)
- Incremental updates (when supported)
- Full snapshot loading
- Change detection and tracking

**Data Source Types:**

```
SQL Database:
  - Connection string with credentials
  - SELECT query returning required fields
  - Optional change detection query

REST API:
  - Base URL and authentication (API key, OAuth)
  - Endpoint path and parameters
  - Response parsing (JSON expected)

HTTP Endpoint:
  - Simple GET request
  - JSON or CSV response
  - Minimal authentication
```

### 2. Processing Engine

**Purpose**: Core business logic for campaign and cycle management.

**Responsibilities:**
- Execute campaign schedules (start new cycles)
- Evaluate record verification status
- Apply escalation rules
- Generate notification queue
- Track cycle progress
- Update verification states

**Key Components:**

**Campaign Scheduler:**
- Uses APScheduler (in-process) or AWS EventBridge (external)
- Triggers new cycle creation per campaign schedule
- Manages cycle lifecycle (start, progress, complete)

**Verification Evaluator:**
- Checks record timestamps against thresholds
- Applies campaign-specific verification logic
- Determines which records need notifications

**Escalation Manager:**
- Tracks escalation levels per cycle
- Determines notification recipients
- Schedules next escalation events
- Handles escalation overflow (repeat last level)

**Notification Queue Builder:**
- Groups records by recipient (one notification per user)
- Applies templates per channel
- Handles contact-less records (escalate to owner)
- Generates delivery tasks

### 3. Output Layer (Notification System)

**Purpose**: Deliver notifications to contacts via configured channels.

**Responsibilities:**
- Send grouped notifications to recipients
- Manage delivery tracking and retry logic
- Handle channel-specific formatting
- Log notification history for audit
- Track delivery status and errors

**Supported Channels:**
- **Email**: SMTP with HTML templates
- **Microsoft Teams**: Webhook or Graph API
- **Slack**: Webhook or API
- **Extensible**: Plugin architecture for new channels

**Delivery Features:**
- Batching: Group notifications where appropriate
- Retry: Configurable retry policy for failures
- Rate Limiting: Respect channel quotas
- Tracking: Delivery confirmation and read receipts (if available)

### 4. State Management (ECHO Database)

**Purpose**: Persist campaign configuration, cycle state, and notification history.

**Schema Categories:**

**Campaign Configuration:**
- Campaign definitions and settings
- Data source connection details
- Escalation rules and templates
- Schedule definitions

**Cycle Tracking:**
- Active and historical cycles
- Cycle state (in-progress, completed)
- Escalation level tracking

**Record Cache:**
- Current snapshot of records per campaign
- Verification status and timestamps
- Contact assignments
- Metadata for template rendering

**Notification History:**
- Sent notifications with recipients
- Delivery status and timestamps
- Response tracking (if applicable)
- Audit trail for compliance

## Data Flow

### Cycle Execution Flow

```
1. CAMPAIGN SCHEDULE TRIGGERS
   └─> Create new Cycle instance

2. INPUT PHASE
   ├─> Connect to data source
   ├─> Fetch current records
   ├─> Transform and validate
   └─> Update record cache in ECHO DB

3. PROCESSING PHASE
   ├─> Evaluate verification status per record
   ├─> Apply escalation rules (level 1)
   ├─> Determine notification recipients
   └─> Build notification queue (grouped by recipient)

4. OUTPUT PHASE
   ├─> Send notifications via channels
   ├─> Log delivery status
   └─> Update notification history

5. WAIT FOR NEXT ESCALATION
   └─> Schedule next escalation event

6. REPEAT STEPS 2-5 FOR EACH ESCALATION LEVEL

7. CYCLE COMPLETION
   ├─> Mark cycle complete
   └─> Archive cycle data
```

### Change Detection Flow

```
1. FETCH CURRENT DATA from source

2. COMPARE WITH CACHED DATA
   ├─> New records: Add to cycle
   ├─> Updated records: Check timestamps
   │   ├─> last_verified changed? → Mark verified
   │   └─> last_updated changed? → Mark unverified
   ├─> Unchanged records: Keep current status
   └─> Removed records: Mark as deleted

3. UPDATE CACHE
   └─> Store current state for next comparison
```

## Integration Patterns

### Data Source Integration

**Read-Only Access Pattern:**
```
ECHO                    External System
  │                            │
  ├─── Query Request ─────────>│
  │                            │ (Read-only view/API)
  │<─── Data Response ─────────┤
  │                            │
  └─── Never writes back ──X   │
```

**Requirements for Data Sources:**
- Unique record identifier
- Contact system IDs (email, employee ID)
- Last updated timestamp (recommended)
- Last verified timestamp (optional, recommended)
- Metadata for notifications (name, description, URL)

### Notification Channel Integration

**Multi-Channel Delivery:**
```
ECHO Notification Queue
       │
       ├──> Email SMTP ──────> Recipients
       ├──> Teams Webhook ───> Recipients
       └──> Slack API ───────> Recipients
```

### Scheduler Integration

**Option 1: APScheduler (In-Process)**
- Simple deployment
- Suitable for single-instance
- Limited scalability

**Option 2: AWS EventBridge (External)**
- Distributed scheduling
- High availability
- Better for multi-instance deployments
- Requires AWS cron format

## Technology Stack (Proposed)

### Backend
- **Framework**: FastAPI (async, automatic API docs)
- **Language**: Python 3.13+
- **Package Manager**: uv (fast, modern)

### Database
- **Primary**: PostgreSQL (rich SQL features, JSON support)
- **ORM**: SQLAlchemy (database abstraction)
- **Migrations**: Alembic (schema versioning)

### Scheduling
- **Development**: APScheduler (in-process)
- **Production**: AWS EventBridge Scheduler (distributed)
- **Cron Format**: AWS cron expressions

### Notification Channels
- **Email**: SMTP (boto3 SES for AWS)
- **Teams**: Microsoft Graph API or webhooks
- **Slack**: Slack API or webhooks

### Template Engine
- **Jinja2**: For HTML email templates and UI rendering

### Deployment
- **Platform**: AWS ECS (containers)
- **Storage**: S3 (templates, exports)
- **Logging**: CloudWatch
- **Monitoring**: CloudWatch metrics and alarms

## Scalability Considerations

### Horizontal Scaling
- Stateless API layer (scale instances)
- External scheduler (EventBridge)
- Database connection pooling
- Async I/O for notifications

### Performance Optimization
- Batch notification delivery
- Cached data source queries
- Indexed database queries
- Lazy loading for large record sets

### Reliability
- Retry policies for notifications
- Dead letter queue for failures
- Transaction rollback on errors
- Graceful degradation

## Security Considerations

### Data Source Access
- Encrypted credentials storage
- Least-privilege access (read-only)
- Connection pooling with limits
- Timeout and rate limiting

### API Security
- Authentication (API keys, OAuth)
- Authorization (role-based access)
- HTTPS only
- Input validation

### Notification Security
- No sensitive data in notification content
- Secure links to source systems
- Audit logging
- PII handling compliance

## Extension Points

### Pluggable Components

1. **Data Source Connectors**
   - Interface: `DataSourceConnector` protocol
   - Implement: SQL, REST, HTTP, custom

2. **Notification Channels**
   - Interface: `NotificationChannel` protocol
   - Implement: Email, Teams, Slack, SMS, custom

3. **Verification Strategies**
   - Interface: `VerificationStrategy` protocol
   - Implement: Timestamp-based, change-based, explicit

4. **Escalation Policies**
   - Interface: `EscalationPolicy` protocol
   - Implement: Linear, exponential, custom

## Deployment Architecture (AWS)

```
┌─────────────────────────────────────────────────────┐
│                   AWS Cloud                         │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  Application Load Balancer                   │  │
│  └────────────────┬─────────────────────────────┘  │
│                   │                                 │
│  ┌────────────────v─────────────────────────────┐  │
│  │  ECS Service (FastAPI instances)             │  │
│  │  ├─ Container 1                              │  │
│  │  ├─ Container 2                              │  │
│  │  └─ Container N                              │  │
│  └────────────────┬─────────────────────────────┘  │
│                   │                                 │
│  ┌────────────────v─────────────────────────────┐  │
│  │  RDS PostgreSQL (ECHO database)              │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  EventBridge Scheduler (campaigns/cycles)    │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  S3 (templates, logs, exports)               │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  CloudWatch (logs, metrics, alarms)          │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```
