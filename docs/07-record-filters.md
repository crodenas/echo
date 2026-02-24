# Record Filters

**Purpose**: This document defines how campaigns select which records need action at each cycle execution.

## Overview

All ECHO campaigns follow the same workflow:
1. Campaign schedule triggers a new cycle
2. ECHO queries the data source
3. **Record filter determines which records need notifications**
4. Notifications are sent with escalation

The **record filter** is the only difference between campaign types (time-based verification vs. contact validation).

## Filter Types

### 1. Time-Based Filter

Selects records that haven't been verified since the cycle started.

**Configuration:**
```json
{
  "filter_type": "time_based",
  "config": {
    "timestamp_field": "last_verified",
    "comparison": "before_cycle_start"
  }
}
```

**Logic:**
```python
def should_include_record(record, cycle_start_date):
    last_verified = record.get("last_verified")
    if last_verified is None:
        return True  # Never verified
    return last_verified < cycle_start_date
```

**Use cases:**
- Quarterly service verification
- Annual database review
- Monthly application inventory check

---

### 2. Contact Validity Filter

Selects records with invalid or missing contact information.

**Configuration:**
```json
{
  "filter_type": "contact_validity",
  "config": {
    "contact_fields": ["owner", "system_custodian"],
    "validation_source": {
      "type": "data_source_provided",  // or "external_api"
      "field_name": "contact_is_valid"
    }
  }
}
```

**Option A: Data Source Provides Validity**
Data source includes a boolean field indicating contact validity:

```sql
-- Data source query
SELECT
  object_id,
  name,
  owner,
  system_custodian,
  (owner IN (SELECT email FROM employee_directory)) AS owner_is_valid,
  (system_custodian IN (SELECT email FROM employee_directory)) AS custodian_is_valid
FROM resources
```

**Filter logic:**
```python
def should_include_record(record):
    # If any contact field is marked invalid, include the record
    return (
        record.get("owner_is_valid") == False or
        record.get("custodian_is_valid") == False
    )
```

**Option B: ECHO Validates Against External API**
ECHO calls an employee directory API to validate contacts.

**See [Employee API Integration](08-employee-api-integration.md) for complete specification.**

**Configuration:**
```json
{
  "filter_type": "contact_validity",
  "config": {
    "contact_fields": ["owner", "system_custodian"],
    "validation_source": {
      "type": "external_api",
      "api_config": {
        "base_url": "https://gateway-intranet.apim.lilly.com",
        "endpoint": "/employees/validate",
        "auth_type": "oauth2",
        "credentials_ref": "arn:aws:secretsmanager:us-east-1:...:secret:employee-api-creds"
      }
    }
  }
}
```

**Employee API Credentials (stored in AWS Secrets Manager):**
```json
{
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "tenant_id": "your-tenant-id",
  "token_endpoint": "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
  "scope": "api://gateway-intranet/.default"
}
```

**Filter Logic:**
```python
async def should_include_record(record, employee_api):
    for field_name in ["owner", "system_custodian"]:
        contact = record.get(field_name)
        if contact:
            is_valid = await employee_api.validate_email(contact)
            if not is_valid:
                return True  # Include if any contact is invalid
    return False
```

**OAuth2 Token Management:**
- Cache access tokens with automatic refresh
- Token expires after ~1 hour (MS Entra default)
- Refresh proactively before expiration
- Handle 401 responses with token refresh retry

**Use cases:**
- Detect services with terminated employee contacts
- Find resources with missing contact assignments
- Identify records where primary contact left the team

---

### 3. Change Detection Filter

Selects records where critical fields have changed since last cycle.

**Configuration:**
```json
{
  "filter_type": "change_detection",
  "config": {
    "monitored_fields": ["name", "description", "owner", "system_custodian"],
    "hash_storage": "cycle_record_hashes"
  }
}
```

**Logic:**
```python
def should_include_record(record, previous_hash):
    current_hash = calculate_hash(record, monitored_fields)
    return current_hash != previous_hash
```

**Use cases:**
- Verify resources after ownership changes
- Re-verify when contact information is updated
- Detect and confirm metadata changes

---

### 4. Composite Filter (OR Logic)

Combine multiple filters - include record if **any** filter matches.

**Configuration:**
```json
{
  "filter_type": "composite",
  "operator": "OR",
  "filters": [
    {
      "filter_type": "time_based",
      "config": {"timestamp_field": "last_verified"}
    },
    {
      "filter_type": "contact_validity",
      "config": {"contact_fields": ["owner"]}
    }
  ]
}
```

**Logic:**
```python
def should_include_record(record, cycle_start):
    # Include if not verified recently OR has invalid contacts
    return (
        time_based_filter(record, cycle_start) or
        contact_validity_filter(record)
    )
```

**Use cases:**
- Comprehensive verification: time-based + contact validation
- Multi-criteria campaigns with flexible inclusion rules

---

## Data Model Changes

### Campaign Table - Add `record_filter` Field

```sql
ALTER TABLE campaigns
ADD COLUMN record_filter JSONB NOT NULL DEFAULT '{
  "filter_type": "time_based",
  "config": {"timestamp_field": "last_verified"}
}';
```

**Example Campaign with Time-Based Filter:**
```json
{
  "id": "550e8400-...",
  "name": "Quarterly Service Verification",
  "campaign_schedule": "cron(0 0 1 */3 ? *)",
  "record_filter": {
    "filter_type": "time_based",
    "config": {
      "timestamp_field": "last_verified",
      "comparison": "before_cycle_start"
    }
  }
}
```

**Example Campaign with Contact Validity Filter:**
```json
{
  "id": "750e8400-...",
  "name": "Invalid Contact Remediation",
  "campaign_schedule": "cron(0 9 * * MON *)",
  "record_filter": {
    "filter_type": "contact_validity",
    "config": {
      "contact_fields": ["owner", "system_custodian"],
      "validation_source": {
        "type": "data_source_provided",
        "field_name_pattern": "{field}_is_valid"
      }
    }
  }
}
```

---

## Verification Semantics

### Time-Based Campaigns
**"Verified" means**: User confirmed the record is accurate

**How verification happens:**
- User clicks "Verify" button → updates `last_verified` timestamp in source system
- OR: User updates record → `last_updated` changes → considered verified
- Next cycle: Record not included because `last_verified >= cycle_start`

### Contact Validity Campaigns
**"Verified" means**: Contacts are now valid in the source system

**How verification happens:**
- User updates contact info in source system
- Next cycle: Data source query no longer returns this record (contacts now valid)
- **No explicit "verify" action needed** - fixing the data resolves the issue

### Change Detection Campaigns
**"Verified" means**: User confirmed the changes are intentional

**How verification happens:**
- User reviews changes and clicks "Verify"
- Next cycle: New hash stored, record only included if changed again

---

## System-Level Configuration

### Employee Directory API

The employee directory API is shared across all campaigns and configured at the system level (not per-campaign).

**Configuration File/Environment:**
```yaml
employee_api:
  enabled: true
  environment: "prod"  # or "dev"
  endpoints:
    dev: "https://gateway-intranet.apim-dev.lilly.com"
    prod: "https://gateway-intranet.apim.lilly.com"
  auth:
    type: "oauth2"
    credentials_ref: "arn:aws:secretsmanager:us-east-1:...:secret:employee-api-creds"
  validation:
    endpoint: "/employees/validate"
    method: "POST"
    batch_size: 100  # Validate multiple emails per request
    cache_ttl: 3600  # Cache validation results for 1 hour
```

**API Client Implementation:**
```python
class EmployeeDirectoryClient:
    def __init__(self, config: dict):
        self.base_url = config["endpoints"][config["environment"]]
        self.auth_config = config["auth"]
        self.token_cache = TokenCache()

    async def get_access_token(self) -> str:
        """Get cached token or refresh if expired."""
        cached_token = self.token_cache.get()
        if cached_token and not cached_token.is_expired():
            return cached_token.access_token

        # Fetch credentials from Secrets Manager
        credentials = await self.secrets_manager.get_secret(
            self.auth_config["credentials_ref"]
        )

        # Request new token from MS Entra
        token_response = await self.oauth2_client.request_token(
            token_endpoint=credentials["token_endpoint"],
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            scope=credentials["scope"]
        )

        # Cache token with expiration
        self.token_cache.set(token_response)
        return token_response["access_token"]

    async def validate_email(self, email: str) -> bool:
        """Check if email is valid in employee directory."""
        token = await self.get_access_token()
        response = await self.http_client.post(
            f"{self.base_url}/employees/validate",
            headers={"Authorization": f"Bearer {token}"},
            json={"email": email}
        )
        return response["is_valid"]

    async def validate_emails_batch(self, emails: list[str]) -> dict[str, bool]:
        """Validate multiple emails in a single request."""
        token = await self.get_access_token()
        response = await self.http_client.post(
            f"{self.base_url}/employees/validate/batch",
            headers={"Authorization": f"Bearer {token}"},
            json={"emails": emails}
        )
        return response["results"]  # {"email@example.com": True, ...}
```

**Performance Optimization:**
- **Batch validation**: Validate all contacts in one request per cycle
- **Result caching**: Cache validation results for 1 hour (configurable)
- **Token reuse**: Cache OAuth2 token until expiration

---

## MVP Scope

**Include in MVP:**
- ✅ Time-Based Filter (timestamp field comparison)
- ✅ Contact Validity Filter - **Option B preferred** (ECHO validates via employee API)
  - Employee directory API already exists with MS Entra OAuth2
  - Centralized validation logic, consistent across campaigns
  - Data sources don't need to implement validation
- ✅ Basic Composite Filter (OR logic for time + contact)

**Defer to MVP+:**
- ⏭️ Contact Validity Filter - Option A (data source provides validity)
  - Can add later if needed for teams without API access
- ⏭️ Change Detection Filter (hash-based)
- ⏭️ Composite Filter with AND/NOT logic
- ⏭️ Custom SQL/expression-based filters

**Rationale for Option B in MVP:**
- Employee API already exists (no new integration needed)
- Single source of truth for contact validation
- Simpler for campaign owners (no need to modify data source queries)
- Consistent validation logic across all campaigns

---

## Implementation Notes

### Filter Evaluation Flow

```python
# Pseudo-code for cycle execution
async def execute_cycle(campaign, cycle):
    # 1. Query data source
    all_records = await fetch_records(campaign.data_source_config)

    # 2. Apply filter
    filter_config = campaign.record_filter
    records_needing_action = []

    for record in all_records:
        if apply_filter(record, filter_config, cycle.start_date):
            records_needing_action.append(record)

    # 3. Group by contact and send notifications
    await send_notifications(records_needing_action, cycle)
```

### Filter Plugin Architecture

Filters should be pluggable for extensibility:

```python
from abc import ABC, abstractmethod

class RecordFilter(ABC):
    @abstractmethod
    def should_include(self, record: dict, context: FilterContext) -> bool:
        """Determine if record should be included in notifications."""
        pass

class TimeBasedFilter(RecordFilter):
    def __init__(self, config: dict):
        self.timestamp_field = config["timestamp_field"]

    def should_include(self, record: dict, context: FilterContext) -> bool:
        last_verified = record.get(self.timestamp_field)
        return last_verified is None or last_verified < context.cycle_start

class ContactValidityFilter(RecordFilter):
    def __init__(self, config: dict):
        self.contact_fields = config["contact_fields"]
        self.validation_config = config["validation_source"]

    def should_include(self, record: dict, context: FilterContext) -> bool:
        # Check if any contact field is invalid
        for field in self.contact_fields:
            validity_field = f"{field}_is_valid"
            if record.get(validity_field) == False:
                return True
        return False
```

---

## Open Questions

### Q1: Contact Validity - How does ECHO know if a contact is invalid?

**✅ DECISION: Use Option B (ECHO validates via employee API)**

**Rationale:**
- Employee directory API already exists (gateway-intranet.apim.lilly.com)
- MS Entra OAuth2 authentication available
- Centralized validation - single source of truth
- Simpler for campaign owners - no need to modify data source queries
- Consistent validation logic across all campaigns

**Implementation:**
- System-level configuration for employee API
- OAuth2 token management with caching
- Batch validation for performance
- Result caching (1 hour TTL)

### Q2: Should contact validity campaigns support explicit "verify" action?

**Option A**: No explicit verify - fixing data resolves the issue
- Fixing contact in source system → next cycle doesn't include record
- Simple, aligns with "read-only" principle

**Option B**: Allow explicit verify even if contact still invalid
- User acknowledges the issue, chooses to defer fixing it
- Useful when fix is complex (e.g., reassigning hundreds of services)

**Recommendation**: Start with Option A. Add Option B if users need to "snooze" invalid contacts.

### Q3: How do we handle records that match multiple filters?

**Example**: Record is both "not verified recently" AND "has invalid contact"

**Option A**: Include once, show all reasons in notification
```
"Your service needs attention because:
- Not verified since 2024-01-01
- Owner email is invalid"
```

**Option B**: Treat as separate notifications (one per filter match)

**Recommendation**: Option A - single notification with all reasons.
