# ECHO Verification Portal Kit

**Status:** Separate Optional Product (Template/Boilerplate)

---

## Overview

The **ECHO Verification Portal Kit** is a standalone template that teams can deploy when their data source doesn't have a UI for users to review and update records.

**This is NOT part of ECHO core.** It's a separate optional product that integrates with ECHO via the verification API.

---

## When You Need It

### ✅ Use Verification Portal Kit If:

- Your data source has no UI (SQL view, REST API, CSV file, etc.)
- Users need to edit data to complete verification
- You want a lightweight, purpose-built verification interface
- You don't want to build a custom UI from scratch

### ❌ You Don't Need It If:

- Your source system has its own UI → Link directly to source system
- Data is read-only → Use ECHO's built-in simple verification page
- You want to build your own custom UI → Build it and call ECHO's verification API
- Users verify by updating source data through other means

---

## Architecture

### How It Fits with ECHO

```
┌─────────────────────────────────────────┐
│  ECHO (Core)                            │
│  - Campaign management                  │
│  - Notifications with links             │
│  - Verification tracking API            │
└─────────────────────────────────────────┘
          ↑
          | Calls /api/verify
          |
┌─────────────────────────────────────────┐
│  Verification Portal (Your Deployment)  │
│  - Reads from your data source          │
│  - Shows edit form                      │
│  - Writes back to data source           │
│  - Calls ECHO API to mark verified      │
└─────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────┐
│  Your Data Source                       │
│  (SQL, API, etc.)                       │
└─────────────────────────────────────────┘
```

### User Flow

```
1. User receives notification from ECHO
   ↓
2. Clicks verification link
   → https://service-portal.company.com/verify?id=service-123&wave=wave-456
   ↓
3. Portal loads record from data source
   ↓
4. Portal shows edit form with current data
   ↓
5. User updates fields (owner, description, etc.)
   ↓
6. Portal validates and saves to data source
   ↓
7. Portal calls ECHO verification API
   POST /api/waves/wave-456/records/service-123/verify
   ↓
8. ECHO marks record as verified
   ↓
9. Next escalation skips this record ✅
```

---

## Quick Start

### 1. Clone the Template

```bash
git clone https://github.com/company/echo-verification-portal-kit
cd echo-verification-portal-kit
```

### 2. Configure for Your Data Source

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml`:

```yaml
portal:
  name: "Service Registry Verification Portal"
  base_url: "https://service-portal.company.com"

data_source:
  type: "sql"  # or "api", "custom"
  connection_string: "postgresql://user:pass@host:5432/dbname"
  table: "services"
  primary_key: "service_id"

  editable_fields:
    - name: "owner_email"
      type: "email"
      required: true
      validation: "^[a-z.]+@company\\.com$"

    - name: "tech_lead"
      type: "string"
      required: true

    - name: "description"
      type: "textarea"
      required: false

    - name: "environment"
      type: "select"
      options: ["production", "staging", "development"]
      required: true

echo_integration:
  api_url: "https://echo.company.com/api"
  auth:
    type: "azure_ad"
    client_id: "${AZURE_CLIENT_ID}"
    client_secret: "${AZURE_CLIENT_SECRET}"

auth:
  type: "azure_ad"
  tenant_id: "${AZURE_TENANT_ID}"
  client_id: "${PORTAL_CLIENT_ID}"
  client_secret: "${PORTAL_CLIENT_SECRET}"
```

### 3. Deploy

```bash
# Using Docker Compose (local/dev)
docker compose up

# Or deploy to your infrastructure
# - AWS ECS/Fargate
# - Azure Container Apps
# - Kubernetes
# - VM with Docker
```

### 4. Configure ECHO Campaign

Update your ECHO campaign to link to the portal:

```python
{
  "name": "Service Verification",
  "verification_url_template": "https://service-portal.company.com/verify?id={object_id}&wave={wave_id}"
}
```

---

## Portal Features

### MVP Features (Out of the Box)

- ✅ **Generic data display** - Read from any SQL/API source
- ✅ **Edit forms** - Configurable fields with validation
- ✅ **Write-back** - Save changes to source
- ✅ **ECHO integration** - Calls verification API automatically
- ✅ **Azure AD auth** - Integrated authentication
- ✅ **Audit trail** - Tracks who changed what
- ✅ **Responsive UI** - Works on desktop and mobile

### Customization Options

Teams can customize:
- **UI/UX** - Templates, styling, branding
- **Field types** - Add custom field types
- **Validation** - Custom validation rules
- **Workflows** - Add approval steps, comments
- **Integrations** - Connect to other systems

---

## Data Source Types

### SQL Database

```yaml
data_source:
  type: "sql"
  connection_string: "${DATABASE_URL}"
  table: "services"
  primary_key: "service_id"
  editable_fields:
    - name: "owner_email"
      type: "email"
```

**How it works:**
- Read: `SELECT * FROM services WHERE service_id = ?`
- Write: `UPDATE services SET owner_email = ? WHERE service_id = ?`

### REST API

```yaml
data_source:
  type: "api"
  base_url: "https://api.company.com"
  read_endpoint: "/services/{id}"
  write_endpoint: "/services/{id}"
  method: "PUT"
  auth:
    type: "bearer_token"
    token: "${API_TOKEN}"
  editable_fields:
    - name: "owner_email"
      json_path: "contacts.owner"
```

**How it works:**
- Read: `GET https://api.company.com/services/{id}`
- Write: `PUT https://api.company.com/services/{id}` with JSON body

### Custom Data Source

Implement the `DataSource` interface:

```python
# custom_source.py

class CustomDataSource:
    def read_record(self, record_id: str) -> dict:
        # Your custom logic to fetch record
        ...

    def write_record(self, record_id: str, updates: dict) -> None:
        # Your custom logic to save changes
        ...
```

---

## Field Types

### Supported Field Types

| Type | HTML Input | Validation | Example |
|------|-----------|------------|---------|
| `string` | `<input type="text">` | Max length, pattern | Name, title |
| `email` | `<input type="email">` | Email format | owner@company.com |
| `textarea` | `<textarea>` | Max length | Description |
| `number` | `<input type="number">` | Min, max | Port number |
| `date` | `<input type="date">` | Date format | Last updated |
| `select` | `<select>` | Options list | Environment |
| `checkbox` | `<input type="checkbox">` | Boolean | Is active |
| `multi-select` | `<select multiple>` | Options list | Tags |

### Field Configuration

```yaml
editable_fields:
  - name: "owner_email"
    type: "email"
    label: "Resource Owner"
    required: true
    validation: "^[a-z.]+@company\\.com$"
    help_text: "Primary person responsible for this resource"

  - name: "environment"
    type: "select"
    label: "Environment"
    required: true
    options:
      - value: "production"
        label: "Production"
      - value: "staging"
        label: "Staging"
      - value: "development"
        label: "Development"

  - name: "tags"
    type: "multi-select"
    label: "Tags"
    required: false
    options: ["critical", "deprecated", "migrating", "legacy"]
```

---

## ECHO Integration

### Verification API

Portal calls ECHO's verification API after user saves:

```python
# After saving to data source
response = requests.post(
    f"{ECHO_API_URL}/api/waves/{wave_id}/records/{record_id}/verify",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "verified_by": user.email,
        "verification_source": "portal",
        "comment": f"Updated via portal: {', '.join(updated_fields)}"
    }
)
```

### Configuration

```yaml
echo_integration:
  api_url: "https://echo.company.com/api"

  # Auth to call ECHO API
  auth:
    type: "azure_ad"
    client_id: "${ECHO_CLIENT_ID}"  # Service principal
    client_secret: "${ECHO_CLIENT_SECRET}"
    scope: "api://echo/.default"
```

---

## Deployment

### Docker Compose (Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  portal:
    build: .
    ports:
      - "8080:8080"
    environment:
      - CONFIG_PATH=/app/config.yaml
      - DATABASE_URL=postgresql://...
      - AZURE_CLIENT_ID=...
      - AZURE_CLIENT_SECRET=...
    volumes:
      - ./config.yaml:/app/config.yaml
```

```bash
docker compose up
```

### AWS ECS Fargate (Production)

```hcl
# Terraform example
resource "aws_ecs_service" "verification_portal" {
  name            = "service-verification-portal"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.portal.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnets
    security_groups = [aws_security_group.portal.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.portal.arn
    container_name   = "portal"
    container_port   = 8080
  }
}
```

### Azure Container Apps

```bash
az containerapp create \
  --name service-verification-portal \
  --resource-group echo-portals \
  --image company.azurecr.io/verification-portal:latest \
  --target-port 8080 \
  --ingress external \
  --env-vars \
    CONFIG_PATH=/app/config.yaml \
    DATABASE_URL=secretref:database-url \
    AZURE_CLIENT_ID=secretref:client-id
```

---

## Security

### Authentication

Portal uses Azure AD (same as ECHO):

```python
# Portal requires authentication
@app.get("/verify")
async def verify_page(
    id: str,
    wave: str,
    user = Depends(get_current_user)  # Azure AD
):
    # Only authenticated users can access
    ...
```

### Authorization

```python
# Check if user can edit this record
def can_edit_record(user, record):
    # Option 1: Owner can edit
    if record["owner_email"] == user["email"]:
        return True

    # Option 2: Admin role can edit
    if "portal.admin" in user["roles"]:
        return True

    # Option 3: Custom logic
    # Check if user is in the owning team, etc.

    return False
```

### Data Protection

- ✅ HTTPS only (TLS/SSL)
- ✅ Azure AD authentication required
- ✅ Authorization checks before edits
- ✅ Audit trail of all changes
- ✅ No sensitive data in logs
- ✅ Connection strings in environment variables

---

## Audit Trail

Portal tracks all changes:

```sql
CREATE TABLE portal_audit_log (
  id UUID PRIMARY KEY,
  record_id VARCHAR(255),
  wave_id VARCHAR(255),

  -- Who and when
  updated_by VARCHAR(255),
  updated_at TIMESTAMP,

  -- What changed
  field_name VARCHAR(100),
  old_value TEXT,
  new_value TEXT,

  -- Context
  user_agent TEXT,
  ip_address VARCHAR(50)
);
```

Query audit log:
```sql
-- See all changes to a record
SELECT * FROM portal_audit_log
WHERE record_id = 'service-123'
ORDER BY updated_at DESC;

-- See all changes by a user
SELECT * FROM portal_audit_log
WHERE updated_by = 'alice@company.com'
ORDER BY updated_at DESC;
```

---

## Customization Examples

### Custom Validation

```python
# custom_validators.py

def validate_service_name(value: str) -> bool:
    """Service names must follow naming convention."""
    pattern = r'^[a-z][a-z0-9-]*[a-z0-9]$'
    return re.match(pattern, value) is not None

# Register custom validator
VALIDATORS = {
    "service_name": validate_service_name
}
```

### Custom Field Type

```python
# custom_fields.py

class EmployeePicker(Field):
    """Custom field to pick employee from directory."""

    def render(self, value):
        return f'''
        <select name="{self.name}" class="employee-picker">
          <option value="">Select employee...</option>
          {self.render_employee_options()}
        </select>
        <script src="/static/employee-picker.js"></script>
        '''

    def render_employee_options(self):
        employees = fetch_employees()  # From employee API
        return '\n'.join([
            f'<option value="{emp.email}">{emp.name}</option>'
            for emp in employees
        ])
```

### Custom Workflow

```python
# Require manager approval for certain changes

@app.post("/verify")
async def submit_verification(updates, user):
    record = get_record(updates.record_id)

    # Check if changes require approval
    if requires_approval(record, updates):
        # Create approval request
        approval = create_approval_request(
            record_id=record.id,
            requested_by=user.email,
            changes=updates
        )

        # Notify manager
        notify_manager(record.owner_manager, approval)

        return {"status": "pending_approval", "approval_id": approval.id}
    else:
        # Apply changes directly
        save_to_source(record.id, updates)
        verify_in_echo(record.id, updates.wave_id, user.email)

        return {"status": "verified"}
```

---

## Maintenance

### Monitoring

Portal exposes metrics:

```
GET /health
{
  "status": "healthy",
  "data_source": "connected",
  "echo_api": "reachable"
}

GET /metrics
# Prometheus format
portal_requests_total 1234
portal_verifications_total 567
portal_errors_total 12
```

### Logging

```python
# Structured logging
logger.info("Verification completed", extra={
    "record_id": record.id,
    "wave_id": wave.id,
    "user": user.email,
    "fields_updated": list(updates.keys())
})
```

### Updates

```bash
# Pull latest template updates
git remote add upstream https://github.com/company/echo-verification-portal-kit
git fetch upstream
git merge upstream/main

# Apply your customizations
# Deploy updated version
```

---

## FAQ

### Q: Do I have to use this portal?
**A:** No, it's optional. Only use it if your data source needs a UI and you don't want to build one from scratch.

### Q: Can I modify it?
**A:** Yes! It's a template. Fork it and customize for your needs.

### Q: Can I use it for multiple data sources?
**A:** Yes, deploy multiple instances with different configurations, or build multi-source support into your fork.

### Q: Does ECHO depend on the portal?
**A:** No. ECHO just sends notifications with URLs. It doesn't care what's at the URL (source system, portal, custom UI, or ECHO's simple page).

### Q: Can I build my own UI instead?
**A:** Absolutely! Just call ECHO's verification API when users verify. The portal is just one option.

### Q: Who maintains the portal?
**A:** Teams deploy and maintain their own portals. The template/kit is maintained centrally, but each deployment is team-owned.

---

## Support

- **Template Issues:** https://github.com/company/echo-verification-portal-kit/issues
- **ECHO Integration:** See ECHO documentation
- **Custom Development:** Contact your team or platform engineering

---

## Summary

The **ECHO Verification Portal Kit** is a standalone template that solves the "my data source has no UI" problem. It's:

- ✅ **Optional** - Only use if you need it
- ✅ **Separate** - Not part of ECHO core
- ✅ **Customizable** - Template to fork and modify
- ✅ **Team-owned** - You deploy and maintain
- ✅ **Integrated** - Calls ECHO's verification API

**ECHO stays focused on orchestration. Portal handles data editing.**
