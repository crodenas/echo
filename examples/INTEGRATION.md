# ECHO Data Integration Example

This document illustrates how ECHO integrates employee directory data with reviewable resources.

## Complete Flow Example

### 1. Data Source (Reviewables1.json)

A service catalog with contact assignments:

```json
{
  "object_id": "obj_779695",
  "last_verified_date": "2025-07-30T20:05:35Z",
  "contact_id_1": "q6l0467",    // SystemId (primary contact)
  "contact_id_2": "t2u5135",    // SystemId (secondary contact)
  "contact_id_3": "f6i3246",    // SystemId (tertiary contact)
  "edit_url": "https://app.example.com/objects/obj_779695/edit"
}
```

### 2. Employee Directory (Employees.json)

Employee records with hierarchy:

```json
{
  "SystemId": "q6l0467",
  "FirstName": "John",
  "LastName": "Smith",
  "InternetEmailAddress": "jsmith@example.com",
  "JobTitle": "Senior Engineer",
  "SupervisorSystemId": "j2y0092"  // Reports to Rosita
}
```

```json
{
  "SystemId": "j2y0092",
  "FirstName": "Rosita",
  "LastName": "Kingstne",
  "InternetEmailAddress": "rkingstne63@creativecommons.org",
  "JobTitle": "Director of Engineering",
  "SupervisorSystemId": "q8r3249"  // Reports to CEO
}
```

```json
{
  "SystemId": "q8r3249",
  "FirstName": "Cortney",
  "LastName": "Larner",
  "InternetEmailAddress": "clarnerea@geocities.com",
  "JobTitle": "Chief Executive Officer",
  "SupervisorSystemId": null  // Top of hierarchy
}
```

### 3. Campaign Configuration

```json
{
  "name": "Service Catalog Verification",
  "data_source": {
    "type": "api",
    "url": "https://api.example.com/reviewables",
    "query_params": {"dataset": "services"}
  },
  "escalation_rules": [
    {
      "level": 0,
      "delay_days": 0,
      "recipients": ["contact_id_1"]
    },
    {
      "level": 1,
      "delay_days": 7,
      "recipients": ["contact_id_1", "contact_id_2"]
    },
    {
      "level": 2,
      "delay_days": 14,
      "recipients": ["contact_id_1.manager", "contact_id_2.manager"]
    }
  ]
}
```

### 4. ECHO Processing

**Level 0 (Day 0):**
- Fetch `obj_779695` from data source
- Resolve recipients: `["contact_id_1"]` → `["q6l0467"]`
- Lookup employee: `q6l0467` → John Smith (`jsmith@example.com`)
- **Send notification to:** jsmith@example.com

**Level 1 (Day 7 - if still unverified):**
- Re-fetch `obj_779695` from data source (fresh lookup)
- Check if verified (compare `last_verified_date` to cycle start)
- If unverified, resolve recipients: `["contact_id_1", "contact_id_2"]` → `["q6l0467", "t2u5135"]`
- Lookup employees and group by recipient
- **Send notifications to:** John Smith, and employee with SystemId t2u5135

**Level 2 (Day 14 - if still unverified):**
- Re-fetch `obj_779695` from data source
- Resolve recipients: `["contact_id_1.manager", "contact_id_2.manager"]`
- For `contact_id_1.manager`:
  1. Get employee `q6l0467` (John Smith)
  2. Get supervisor `j2y0092` (Rosita Kingstne)
  3. Email: `rkingstne63@creativecommons.org`
- For `contact_id_2.manager`:
  1. Get employee `t2u5135`
  2. Get their supervisor
  3. Email: supervisor's email
- **Send notifications to:** Rosita Kingstne (John's manager) and the other manager

### 5. Manager Hierarchy Traversal

```
obj_779695
├─ contact_id_1: q6l0467 (John Smith)
│  └─ manager: j2y0092 (Rosita Kingstne)
│     └─ manager: q8r3249 (Cortney Larner, CEO)
│        └─ manager: null (top of hierarchy)
│
├─ contact_id_2: t2u5135 (Employee 2)
│  └─ manager: ... (their supervisor)
│
└─ contact_id_3: f6i3246 (Employee 3)
   └─ manager: ... (their supervisor)
```

## Key Integration Points

1. **Contact Resolution:**
   - Data source uses `SystemId` values in contact fields
   - ECHO queries Employee API to get email addresses
   - No employee data stored in ECHO (fresh lookup each time)
   - **Note:** Employee API data refreshes every 24 hours (exact time unknown)
   - Employee data may be up to 24 hours stale

2. **Manager Hierarchy:**
   - `SupervisorSystemId` links employee to their manager
   - Supports multi-level escalations (`contact.manager.manager`)
   - Gracefully handles top of hierarchy (null supervisor)

3. **Fresh Lookup (Decision #12):**
   - Re-fetch data from source at each escalation
   - Re-resolve contacts via Employee API
   - Ensures notifications go to current owners
   - Handles mid-cycle personnel changes

## Data Flow Diagram

```
┌────────────────────┐
│  Data Source API   │  Reviewables1.json (obj_779695)
│  (Reviewables)     │  contact_id_1: "q6l0467"
└─────────┬──────────┘
          │
          │ 1. Fetch records
          ▼
┌────────────────────┐
│   ECHO Processing  │
│      Engine        │
└─────────┬──────────┘
          │
          │ 2. Resolve SystemId → Employee
          ▼
┌────────────────────┐
│  Employee API      │  Employees.json
│  (Azure Protected) │  SystemId: "q6l0467"
└─────────┬──────────┘  InternetEmailAddress: "jsmith@..."
          │             SupervisorSystemId: "j2y0092"
          │
          │ 3. Get manager (if needed)
          ▼
┌────────────────────┐
│  Employee API      │  Employees.json
│  (Azure Protected) │  SystemId: "j2y0092"
└─────────┬──────────┘  InternetEmailAddress: "rkingstne63@..."
          │
          │ 4. Send notifications
          ▼
┌────────────────────┐
│ Notification       │  Email: jsmith@example.com
│ Channels           │  Email: rkingstne63@creativecommons.org
└────────────────────┘
```

## See Also

- `docs/decisions.md` - Decision #13: Employee Directory Integration
- `docs/02-architecture.md` - Employee Directory Integration section
- `docs/03-data-model.md` - Contact field requirements
- `examples/README.md` - Employee data structure details
