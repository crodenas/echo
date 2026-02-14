# Core Concepts

This document defines the fundamental concepts and terminology used throughout ECHO.

## Primary Entities

### Campaign

A **Campaign** defines a continuous verification process for a specific set of resources.

**Key Attributes:**
- **Name and Description**: Human-readable identification
- **Data Source**: Connection details for inventory data (SQL, API, HTTP)
- **Campaign Schedule**: How often to start new verification cycles
- **Cycle Schedule**: Notification timing within each cycle
- **Escalation Rules**: Who to notify, when, and how many times
- **Notification Templates**: Message content per channel (email, Teams, Slack)
- **Enabled/Disabled**: Active status flag

**Lifecycle:**
- Created by campaign owner (typically a team lead)
- Runs continuously while enabled
- Automatically starts new cycles per schedule
- Can be paused/resumed or deleted

**Example:**
```json
{
  "name": "Q1 Service Verification",
  "description": "Quarterly verification of all production services",
  "data_source": {
    "type": "sql",
    "connection": "...",
    "query": "SELECT * FROM services_view"
  },
  "campaign_schedule": "cron(0 0 1 */3 ? *)",  // Every 3 months
  "cycle_schedule": "cron(0 12 * * ? *)",       // Daily at noon
  "escalation_count": 3,
  "enabled": true
}
```

### Cycle

A **Cycle** is a single execution instance of a campaign.

**Key Attributes:**
- **Start Date**: When the cycle began
- **End Date**: When the cycle completes (based on escalation schedule)
- **Campaign Reference**: Which campaign spawned this cycle
- **Records**: Snapshot of reviewable items at cycle start
- **Escalation Level**: Current notification phase (1, 2, 3, etc.)
- **Completion Status**: In-progress, completed, or cancelled

**Lifecycle:**
1. Created automatically by campaign schedule
2. Loads current records from data source
3. Sends notifications based on escalation schedule
4. Tracks verification progress
5. Completes when all records verified or max escalations reached

**Duration:**
- Determined by escalation count and notification frequency
- Example: 3 escalations, weekly = 3 weeks total
- Must be shorter than campaign frequency to avoid overlap

### Record (Reviewable Item)

A **Record** represents a single resource that needs verification.

**Key Attributes:**
- **Object Identifier**: Unique ID from source system
- **Metadata**: Resource details (name, type, description, etc.)
- **Contacts**: System IDs of responsible users
- **Last Updated Date**: When the resource was last modified
- **Last Verified Date**: When the resource was last confirmed accurate
- **Verification Status**: Verified, unverified, or stale

**Verification States:**
- **Verified**: Confirmed accurate in current cycle
- **Unverified**: Not yet confirmed in current cycle
- **Stale**: Not verified within defined time threshold

**Example:**
```json
{
  "object_id": "service-123",
  "name": "Payment Processing API",
  "type": "service",
  "contacts": ["alice@example.com", "bob@example.com"],
  "last_updated": "2024-01-15",
  "last_verified": "2024-01-10",
  "metadata": {
    "url": "https://portal.example.com/services/123",
    "owner_team": "payments"
  }
}
```

### Contact

A **Contact** is a user responsible for verifying one or more records.

**Key Attributes:**
- **System ID**: User identifier (email, employee ID, etc.)
- **Name**: Display name
- **Assigned Records**: Which resources they're responsible for
- **Notification Preferences**: Channel preferences (if supported)

**Notification Grouping:**
- Single notification per user per escalation level
- Contains all records assigned to that user
- Reduces notification fatigue
- Improves efficiency (verify all items at once)

## Supporting Concepts

### Escalation

An **Escalation** defines a notification event within a cycle.

**Components:**
- **Level**: Sequential number (1, 2, 3, etc.)
- **Recipients**: Who receives notifications at this level
  - Record contacts (default)
  - Static users (e.g., team leads)
  - Manager hierarchy (if available)
- **Delay**: Time offset from cycle start

**Example:**
```json
{
  "escalations": [
    {
      "level": 1,
      "recipients": ["record_contacts"],
      "delay_days": 0
    },
    {
      "level": 2,
      "recipients": ["record_contacts"],
      "delay_days": 7
    },
    {
      "level": 3,
      "recipients": ["record_contacts", "team_lead@example.com"],
      "delay_days": 14
    }
  ]
}
```

### Notification

A **Notification** is a message sent to a contact about their records.

**Components:**
- **Recipient**: Contact who receives the message
- **Channel**: Delivery method (email, Teams, Slack)
- **Records**: List of items requiring verification
- **Template**: Message content and formatting
- **Escalation Level**: Which escalation triggered this notification
- **Delivery Status**: Pending, sent, delivered, failed

### Data Source

A **Data Source** defines how ECHO accesses inventory data.

**Types:**
- **SQL Database**: Direct database connection with query
- **REST API**: HTTP endpoint with authentication
- **HTTP Endpoint**: Simple HTTP GET returning JSON/CSV

**Requirements:**
- Must be read-only (ECHO never writes back)
- Must return required fields (object_id, contacts, timestamps)
- Should provide change detection mechanism

## Shared Responsibility Model

### ECHO's Responsibilities
- Orchestrate notification campaigns
- Track verification status
- Manage escalation schedules
- Deliver notifications
- Provide campaign management interface

### Team's Responsibilities
- Maintain source data accuracy
- Provide read-only data access
- Update resource metadata in their own systems
- Respond to verification notifications
- Configure campaign parameters

**Critical Principle**: ECHO never modifies source data. Teams retain full ownership and control of their inventory systems.

## Terminology Quick Reference

| Term | Definition |
|------|------------|
| **Campaign** | Continuous verification process for a set of resources |
| **Cycle** | Single execution of a campaign |
| **Record** | Individual resource requiring verification |
| **Contact** | User responsible for verifying records |
| **Escalation** | Notification event at a specific level and time |
| **Notification** | Message sent to a contact about their records |
| **Data Source** | External system containing inventory data |
| **Reviewable Item** | Synonym for Record |
| **Object** | Synonym for Record |
