
# ECHO System Design

ECHO is an enterprise software system designed to help teams manage and verify resource inventory data through automated notification cycles. The system enables teams to maintain data accuracy by sending periodic verification requests to resource contacts without requiring changes to existing data sources.

## Table of Contents
1. [System Overview](#system-overview)
2. [Minimal Requirements](#minimal-requirements)
3. [Core Concepts](#core-concepts)
4. [Design Principles](#design-principles)
5. [System Architecture](#system-architecture)
6. [Data Model](#data-model)
7. [Workflow](#workflow)
8. [Extensibility](#extensibility)
9. [Open Questions](#open-questions)

## System Overview

ECHO serves as a verification orchestration layer that:
- Connects to existing team data sources in read-only mode
- Manages periodic verification campaigns for resource inventories
- Sends targeted notifications to responsible contacts
- Tracks update or verification status and escalation cycles
- Maintains its own state without modifying source data

### Key Benefits
- **Minimal Integration Impact**: Requires only read-only access to existing data sources
- **Data Ownership Preservation**: Teams retain full control of their source data
- **Notification as a Service**: Provides centralized notification orchestration, allowing teams to leverage shared infrastructure and templates without building their own notification systems
- **Multi-tenancy**: Supports multiple teams and campaigns simultaneously

## Minimal Requirements

To implement and operate ECHO effectively, the following minimal requirements must be met:

### Data Access Requirements
- **Read-only view to inventory data**: ECHO requires access to view resource inventory data from existing team systems without modification privileges
- **Record identifier**: Each resource record must have a unique identifier that can be consistently referenced across verification cycles
- **Defined contacts**: Each resource record must have associated contact information identifying who should receive verification notifications
- **Change detection mechanism**: The data source should provide a way to detect changes to records

### Team Integration Requirements
- **Existing portal/process dependency**: ECHO relies on the team's existing portal or process to update and verify metadata - ECHO does not provide data editing capabilities
- **Data source maintenance**: Teams remain responsible for maintaining the accuracy and completeness of their source data systems

### Notification Infrastructure Requirements
- **Templates for supported transports**: Each notification channel (email, Teams, Slack, etc.) requires predefined templates that can be customized per campaign
- **Delivery mechanism**: Appropriate infrastructure must be in place to support the chosen notification methods (SMTP servers, API access, etc.)

## Core Concepts

### Campaign
A **Campaign** defines a verification process for a specific set of resources:
- **Scope**: Group of resources to be verified together
- **Data Source**: Connection to team's inventory system
- **Schedule**: Frequency for starting new verification cycles
- **Lifecycle**: Runs continuously until explicitly disabled
- **Escalation Rules**: Defines notification recipients and timing

### Cycle
A **Cycle** is a single execution of a campaign:
- **Duration**: Determined by campaign frequency and escalation count
- **States**: Start date, escalation schedule, and completion criteria
- **Records**: Set of resources being verified in this cycle
- **Notifications**: Generated based on escalation rules and contact assignments

### Record
A **Record** represents a single resource item from the data source:
- **Identity**: Unique identifier from source system
- **Contacts**: Associated users responsible for verification
- **Verification States**:
  - *Verified*: Confirmed as accurate (via explicit confirmation or "last verified" timestamp)
  - *Unverified*: Not confirmed in current cycle
  - *Stale*: Not verified within defined time period

### Contact
A **Contact** is a user associated with one or more records:
- **Identity**: System ID
- **Responsibilities**: Which records they can verify
- **Notification Preferences**: How and when to receive notifications

## Design Principles

### 1. Data Source Independence
- **Read-Only Access**: ECHO never modifies source data
- **Minimal Requirements**: Requires only essential fields for operation
- **Source of Truth**: Teams maintain control of their data
- **Flexible Integration**: Supports SQL databases, REST APIs, HTTP endpoints

### 2. Enhanced Integration Support
- **Verification Timestamps**: Source systems can provide "last verified" dates
- **Change Detection**: Multiple methods to detect data updates
- **Metadata Enrichment**: Additional fields improve verification resolution

### 3. Flexible Notification System
- **User Grouping**: Single notification per user with all their records
- **Multiple Channels**: Email, Teams, Slack, etc.
- **Custom Templates**: Teams can customize notification content and format
- **Source Links**: Notifications direct users to authoritative data source

## System Architecture

### Core Components

#### 1. Data Ingestion Layer
**Input Component**
- Pulls data from configured data sources
- Updates ECHO's internal database
- Supports multiple data source types and authentication methods
- Handles data transformation and validation

#### 2. Processing Engine
**Processing Component**
- Manages record verification state
- Implements campaign and cycle logic
- Queues notifications based on escalation rules
- Tracks verification progress and timing

#### 3. Notification System
**Output Component**
- Groups notifications by recipient
- Sends notifications via configured channels
- Manages delivery tracking and retry logic
- Supports multiple notification methods simultaneously

#### 4. State Management
**ECHO Database**
- Maintains campaign and cycle definitions
- Tracks record verification states
- Stores notification history and delivery status
- Manages user preferences and contact mappings

### Cycle Execution Flow

Each cycle execution follows a three-phase process:

1. **Input Phase**
   - Sync data from source systems
   - Update ECHO's database with current resource state
   - Identify new, modified, or removed records

2. **Processing Phase**
   - Evaluate verification status for each record
   - Apply campaign escalation rules
   - Generate notification queue grouped by recipient
   - Update cycle state and tracking information

3. **Output Phase**
   - Send grouped notifications to contacts
   - Log notification history for audit trails

## Data Model

### Campaign Configuration
- Campaign ID and metadata
- Data source connection details
- Cycle frequency and timing
- Escalation configuration and recipient lists
- Notification templates and channels

### Record Tracking
- Source record identifier and metadata
- Current verification status and timestamps
- Associated contact mappings
- Cycle participation history

### Notification Management
- Notification queue and delivery status
- User preferences and contact information
- Escalation tracking and timing
- Delivery confirmations and responses

## Workflow

### Campaign Setup
1. Team configures data source connection
2. Defines campaign parameters (frequency, escalation rules)
3. Maps notification recipients and escalation paths
4. Configures notification templates and channels

### Cycle Execution
1. **Data Synchronization**: Pull latest data from source
2. **State Assessment**: Evaluate verification status for each record
3. **Notification Generation**: Create notifications based on escalation rules
4. **Delivery**: Send grouped notifications to contacts
5. **Tracking**: Monitor responses and update verification status

### Escalation Handling
- **Recipients**: Support for static users, record contacts, or management hierarchy
- **Overflow**: Last defined recipients handle additional escalations
- **Customization**: Flexible escalation patterns per campaign

## Extensibility

### Data Source Support
- SQL databases with custom queries
- REST APIs with authentication
- HTTP endpoints with various data formats
- Custom connectors for specific systems

### Notification Channels
- Email with customizable templates
- Microsoft Teams integration
- Slack messaging
- Custom notification providers

## Open Questions

### Record Verification Edge Cases
**Problem**: How to handle records with no valid contacts for notifications?

**Options**:
1. **Skip and Retry**: Leave unverified until next cycle
2. **Escalate to Owner**: Notify campaign owner with orphaned records list
3. **Default Contacts**: Assign fallback contacts for orphaned records

### Verification Confirmation Methods
**Problem**: How should ECHO detect that a record has been verified?

**Approaches**:
1. **Source Timestamps**: Rely on "last verified" fields in source data
2. **Change Detection**: Monitor for data modifications as proxy for verification
3. **Explicit Confirmation**: Require explicit user confirmation via ECHO interface
4. **Hybrid Approach**: Support multiple detection methods per campaign

### Cycle Overlap Management
**Problem**: What happens if a new cycle starts before the previous one completes?

**Considerations**:
- Campaign frequency should be longer than cycle duration to prevent overlap
- System should prevent or handle overlapping cycles
- Need clear policies for cycle conflict resolution
