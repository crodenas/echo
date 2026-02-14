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
- **Notification Templates**: Message content and URL patterns per channel (email, Teams, Slack)
- **Enabled**: Active status flag (true/false)

**Status Behavior:**
- **Enabled (true)**: Creates new cycles on schedule, executes escalations for in-progress cycles
- **Disabled (false)**: Stops creating new cycles; in-progress cycles continue to completion
- Campaign schedule remains in scheduler but skips execution when disabled
- Re-enabling: Starts fresh on next scheduled cycle (doesn't resume or catch up)
- Manual intervention: Cycle schedules can be manually deleted if immediate cancellation needed

**Lifecycle:**
- Created by campaign owner (typically a team lead)
- Runs continuously while enabled
- Automatically starts new cycles per schedule
- Can be disabled or deleted

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
  "campaign_schedule": "cron(0 0 1 */3 ? *)",  // Every 3 months (starts new cycles)
  "escalation_rules": [                         // Escalations within each cycle
    {"level": 0, "delay_days": 0},              // Initial notification
    {"level": 1, "delay_days": 7},              // First reminder
    {"level": 2, "delay_days": 14}              // Second reminder
  ],
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
- **Current Escalation Level**: Current notification phase (0, 1, 2, etc.)
- **Completion Status**: In-progress, completed, or cancelled

**Lifecycle:**
1. Created automatically by campaign schedule
2. Loads current records from data source
3. Sends notifications based on escalation schedule
4. Tracks verification progress
5. Completes when all records verified or max escalations reached

**Duration:**
- Determined by escalation count and notification frequency
- Example: 3 escalations at day 0, 7, 14 = 14 days total
- Must be shorter than campaign frequency to avoid overlap

### Record (Reviewable Item)

A **Record** represents a single resource that needs verification.

**Key Attributes:**
- **Object Identifier**: Unique ID from source system
- **Metadata**: Resource details (name, type, description, etc.)
- **Contact Fields**: Role-specific contact identifiers (field names defined by source system)
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
  "owner": "alice@example.com",
  "system_custodian": "bob@example.com",
  "primary_it_contact": "charlie@example.com",
  "last_updated": "2024-01-15",
  "last_verified": "2024-01-10",
  "environment": "production"
}
```

**Note on Contact Fields:**
- Field names are defined by the source system (e.g., `owner`, `system_custodian`, `primary_it_contact`)
- Each contact field contains a single contact identifier (email, user ID, etc.), not an array
- Different data sources may use different role names based on organizational terminology
- ECHO requires at least one contact field per record
- Campaign owners configure which contact fields to use for notifications at each escalation level
- If multiple people share a responsibility, the source system should define separate fields (e.g., `owner` and `backup_owner`)

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
- **Level**: Sequential number starting at 0
  - Level 0: Initial notification (not an escalation)
  - Level 1+: Actual escalations/reminders
- **Recipients**: Who receives notifications at this level (specified by name)
  - Contact field names from data source (e.g., `owner`, `system_custodian`)
  - Manager hierarchy (e.g., `owner.manager`, `system_custodian.manager`)
  - Static email addresses (e.g., `team_lead@example.com`)
- **Delay**: Time offset from cycle start

**Example:**
```json
{
  "escalations": [
    {
      "level": 0,
      "recipients": ["owner"],
      "delay_days": 0
    },
    {
      "level": 1,
      "recipients": ["owner", "system_custodian"],
      "delay_days": 7
    },
    {
      "level": 2,
      "recipients": ["owner", "system_custodian", "owner.manager"],
      "delay_days": 14
    }
  ]
}
```

**Recipient Types:**
- **Contact field names**: Reference fields from data source (e.g., `owner`, `system_custodian`)
- **Manager hierarchy**: Append `.manager` to any contact field (e.g., `owner.manager`)
- **Static emails**: Direct email addresses (e.g., `team_lead@example.com`)
```

### Notification

A **Notification** is a message sent to a contact about their records.

**Components:**
- **Recipient**: Contact who receives the message
- **Channel**: Delivery method (email, Teams, Slack)
- **Records**: List of items requiring verification
- **Template**: Message content and formatting (Jinja2)
- **Escalation Level**: Which escalation triggered this notification
- **Delivery Status**: Pending, sent, delivered, failed

**Template Configuration:**
Each notification channel references a Jinja2 template by ID. Template authors have full control over:
- **Record display**: Show all inline, summary + link, or hybrid approach
- **URL formatting**: Embed URLs directly in template using Jinja2 syntax
- **Layout and styling**: Design appropriate for their audience and record volume

**Example approaches:**
- Small lists: Display all records inline in email body
- Large lists: Show summary ("You have 47 items") + link to view all
- Hybrid: Show first N records + "and X more" link

### Data Source

A **Data Source** defines how ECHO accesses inventory data.

**Types:**
- **SQL Database**: Direct database connection with query
- **REST API**: HTTP endpoint with authentication
- **HTTP Endpoint**: Simple HTTP GET returning JSON/CSV

**Requirements:**
- Must be read-only (ECHO never writes back)
- Must return required fields:
  - `object_id`: Unique identifier for each record
  - At least one contact field (field name defined by source system)
  - Optional: `last_updated`, `last_verified` timestamps
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
