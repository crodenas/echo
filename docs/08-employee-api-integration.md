# Employee API Integration

**Purpose**: Define the interface contract between ECHO and the Employee Directory API (OData) for contact validation.

## API Details

**API Type:** OData v4

**Environments:**
- **Dev**: `https://gateway-intranet.apim-dev.lilly.com/workforce_fastapi/GWF_Workers`
- **Prod**: `https://gateway-intranet.apim.lilly.com/workforce_fastapi/GWF_Workers`

**Authentication:** Microsoft Entra OAuth2 (client credentials flow)

**Credentials Required:**
- `client_id` - Application client ID (from app registration)
- `client_secret` - Application secret
- `tenant_id` - Azure AD tenant ID

**Token Endpoint:**
```
https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token
```

**Scope:**
```
api://gateway-intranet/.default
```

---

## Employee Data Schema

**Note:** While the API returns 170+ fields, ECHO only models the fields it needs using Pydantic models for type safety.

**Key Fields for ECHO:**

| Field | Type | Description | Example | Usage |
|-------|------|-------------|---------|-------|
| `GlobalId` | Integer | Unique employee identifier | `2151868` | Primary key |
| `SystemLogonId` | String | Network username | `"V5X1868"` | Alternate lookup |
| `InternetEmailAddress` | String | Employee email (uppercase) | `"CRODENAS@LILLY.COM"` | **Primary validation field** |
| `StatusCode` | String | Employee status code | `"3"` | Active = "3" |
| `StatusDescription` | String | Human-readable status | `"Active"` | Active employees only |
| `GroupCode` | String | Worker group code | `"A"` | A = Employee |
| `GroupDescription` | String | Worker group | `"Employee"` | "Employee", "Contractor", etc. |
| `TerminationDate` | Date | Termination date (null if active) | `null` | Must be null for active |
| `FirstName` | String | First name | `"Christopher"` | Display name |
| `LastName` | String | Last name | `"Rodenas"` | Display name |
| `FriendlyFirstName` | String | Preferred first name | `"Chris"` | Preferred display |
| `SupervisorEmail` | String | Manager's email | `"aesslinger@lilly.com"` | **For manager escalation** |
| `SupervisorGlobalId` | Integer | Manager's GlobalId | `2151304` | Manager lookup |

**Full Schema:** 170+ fields available (see example response for complete list)

---

## Pydantic Data Models

ECHO uses Pydantic models for type safety and validation. Only the fields ECHO needs are modeled (not all 170+).

**Note:** Since we filter for active employees at query time (`StatusCode='3' and TerminationDate=null`), we don't need to model status fields - all returned employees are guaranteed active.

### Employee Models

```python
# src/integrations/employee_api/models.py

from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class EmployeeBase(BaseModel):
    """Core employee fields (minimal set).

    Note: StatusCode and TerminationDate not modeled since we filter
    for active employees at query time.
    """
    global_id: int = Field(alias="GlobalId")
    system_logon_id: str = Field(alias="SystemLogonId")
    internet_email_address: EmailStr = Field(alias="InternetEmailAddress")

    model_config = {"populate_by_name": True}


class Employee(EmployeeBase):
    """Full employee record with all fields ECHO uses.

    All employees are guaranteed active (filtered at query time).
    """
    # Name fields (all optional - prioritize Friendly, fall back to regular)
    first_name: Optional[str] = Field(None, alias="FirstName")
    last_name: Optional[str] = Field(None, alias="LastName")
    friendly_first_name: Optional[str] = Field(None, alias="FriendlyFirstName")
    friendly_last_name: Optional[str] = Field(None, alias="FriendlyLastName")

    group_code: Optional[str] = Field(None, alias="GroupCode")
    group_description: Optional[str] = Field(None, alias="GroupDescription")

    # Manager/escalation fields
    supervisor_email: Optional[EmailStr] = Field(None, alias="SupervisorEmail")
    supervisor_global_id: Optional[int] = Field(None, alias="SupervisorGlobalId")
    supervisor_first_name: Optional[str] = Field(None, alias="SupervisorFirstName")
    supervisor_last_name: Optional[str] = Field(None, alias="SupervisorLastName")

    @property
    def display_name(self) -> str:
        """Get display name, prioritizing Friendly names over formal names.

        Priority:
        1. FriendlyFirstName + FriendlyLastName (e.g., "Chris Rodenas")
        2. FirstName + LastName (e.g., "Christopher Rodenas")
        3. Email address (fallback if no names available)
        """
        # Priority 1: Friendly names (preferred)
        if self.friendly_first_name and self.friendly_last_name:
            return f"{self.friendly_first_name} {self.friendly_last_name}"

        # Priority 2: Formal names (fallback)
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"

        # Priority 3: Email (last resort)
        return str(self.internet_email_address)

    @property
    def first_name_preferred(self) -> str:
        """Get preferred first name (Friendly or regular)."""
        return self.friendly_first_name or self.first_name or str(self.internet_email_address).split('@')[0]

    @property
    def last_name_preferred(self) -> str:
        """Get preferred last name (Friendly or regular)."""
        return self.friendly_last_name or self.last_name or ""


class EmployeeValidationResult(BaseModel):
    """Result of email validation.

    Simple model since we filter for active at query time:
    - is_valid=True: Active employee found
    - is_valid=False: Employee not found OR inactive/terminated
    """
    email: EmailStr
    is_valid: bool
    employee: Optional[Employee] = None  # Full employee data if valid


class ODataResponse(BaseModel):
    """OData API response envelope."""
    odata_count: int = Field(alias="@odata.count")
    value: list[Employee]

    model_config = {"populate_by_name": True}
```

### Usage Examples

**Name Prioritization (Friendly → Formal → Email):**
```python
# Example 1: Both Friendly and Formal names available
employee = Employee(
    GlobalId=2151868,
    SystemLogonId="V5X1868",
    InternetEmailAddress="CRODENAS@LILLY.COM",
    StatusCode="3",
    StatusDescription="Active",
    FirstName="Christopher",
    LastName="Rodenas",
    FriendlyFirstName="Chris",      # ← Prioritized
    FriendlyLastName="Rodenas"       # ← Prioritized
)
print(employee.display_name)  # → "Chris Rodenas" (uses Friendly)
print(employee.first_name_preferred)  # → "Chris"

# Example 2: Only Formal names available
employee = Employee(
    GlobalId=1234567,
    InternetEmailAddress="john.smith@lilly.com",
    FirstName="John",           # ← Used as fallback
    LastName="Smith",           # ← Used as fallback
    StatusCode="3",
    StatusDescription="Active"
)
print(employee.display_name)  # → "John Smith" (uses FirstName/LastName)

# Example 3: No names available (edge case)
employee = Employee(
    GlobalId=9999999,
    InternetEmailAddress="noreply@lilly.com",
    StatusCode="3",
    StatusDescription="Active"
)
print(employee.display_name)  # → "noreply@lilly.com" (email fallback)
```

**Parsing OData Response:**
```python
response = await http_client.get(odata_url)
odata_response = ODataResponse(**response.json())

for employee in odata_response.value:
    print(f"{employee.display_name} - {employee.internet_email_address}")
    if employee.is_active:
        print(f"Manager: {employee.supervisor_email}")
```

**Validation Result:**
```python
result = await employee_client.validate_email("crodenas@lilly.com")

if result.is_valid:
    print(f"Valid employee: {result.employee.display_name}")
    print(f"Manager: {result.employee.supervisor_email}")
else:
    print(f"Invalid: {result.reason}")  # "terminated", "not_found", etc.
```

---

## OData Query Operations

## OData Query Operations

### 1. Validate Single Email

**Purpose**: Check if an email address belongs to an active employee.

**Strategy**: Filter for active employees **on the server** to reduce data transfer and simplify logic.

**Query (with active filter):**
```
GET /workforce_fastapi/GWF_Workers?$filter=InternetEmailAddress eq 'CRODENAS@LILLY.COM' and StatusCode eq '3' and TerminationDate eq null&$select=GlobalId,SystemLogonId,InternetEmailAddress,FirstName,LastName,FriendlyFirstName,FriendlyLastName,SupervisorEmail&$top=1
```

**OData Filter Breakdown:**
- `InternetEmailAddress eq 'CRODENAS@LILLY.COM'` - Match email
- `and StatusCode eq '3'` - Only active employees
- `and TerminationDate eq null` - Not terminated
- `$select` - Return only needed fields (no StatusCode/TerminationDate needed since we filtered)
- `$top=1` - Limit to 1 result (email should be unique)

**Request Example:**
```http
GET /workforce_fastapi/GWF_Workers?$filter=InternetEmailAddress eq 'CRODENAS@LILLY.COM' and StatusCode eq '3' and TerminationDate eq null&$select=GlobalId,InternetEmailAddress,FirstName,LastName,FriendlyFirstName,FriendlyLastName,SupervisorEmail&$top=1 HTTP/1.1
Host: gateway-intranet.apim.lilly.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6...
Accept: application/json
```

**Response (Active Employee Found):**
```json
{
  "@odata.count": 1,
  "value": [
    {
      "GlobalId": 2151868,
      "SystemLogonId": "V5X1868",
      "InternetEmailAddress": "CRODENAS@LILLY.COM",
      "FirstName": "Christopher",
      "LastName": "Rodenas",
      "FriendlyFirstName": "Chris",
      "FriendlyLastName": "Rodenas",
      "SupervisorEmail": "aesslinger@lilly.com"
    }
  ]
}
```

**Response (Employee Not Found OR Inactive/Terminated):**
```json
{
  "@odata.count": 0,
  "value": []
}
```

**Note:** If the employee is inactive or terminated, the filter excludes them and returns 0 results. This is intentional - we can't contact inactive employees, so they're treated the same as "not found".

**Simplified Validation Logic:**
```python
def is_valid_employee(response: dict) -> bool:
    """Determine if employee is valid (active).

    Simple: If found (after active filter) = valid, else invalid.
    """
    return response["@odata.count"] > 0
```

---

### 2. Validate Multiple Emails (Batch)

**Purpose**: Validate multiple email addresses in a single request using OData `$filter` with OR conditions.

**Query (up to 20 emails recommended per request):**
```
GET /workforce_fastapi/GWF_Workers?$filter=InternetEmailAddress in ('EMAIL1@LILLY.COM','EMAIL2@LILLY.COM','EMAIL3@LILLY.COM')&$select=InternetEmailAddress,StatusCode,StatusDescription,TerminationDate,SupervisorEmail
```

**Alternative using OR conditions:**
```
GET /workforce_fastapi/GWF_Workers?$filter=InternetEmailAddress eq 'EMAIL1@LILLY.COM' or InternetEmailAddress eq 'EMAIL2@LILLY.COM'&$select=InternetEmailAddress,StatusCode,StatusDescription,TerminationDate
```

**Request Example:**
```http
GET /workforce_fastapi/GWF_Workers?$filter=InternetEmailAddress in ('CRODENAS@LILLY.COM','AESSLINGER@LILLY.COM')&$select=GlobalId,InternetEmailAddress,StatusCode,StatusDescription,TerminationDate,SupervisorEmail HTTP/1.1
Host: gateway-intranet.apim.lilly.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6...
Accept: application/json
```

**Response:**
```json
{
  "@odata.count": 2,
  "value": [
    {
      "GlobalId": 2151868,
      "InternetEmailAddress": "CRODENAS@LILLY.COM",
      "StatusCode": "3",
      "StatusDescription": "Active",
      "TerminationDate": null,
      "SupervisorEmail": "aesslinger@lilly.com"
    },
    {
      "GlobalId": 2151304,
      "InternetEmailAddress": "AESSLINGER@LILLY.COM",
      "StatusCode": "3",
      "StatusDescription": "Active",
      "TerminationDate": null,
      "SupervisorEmail": "somemanager@lilly.com"
    }
  ]
}
```

**Batch Validation Logic:**
```python
async def validate_emails_batch(emails: list[str]) -> dict[str, bool]:
    """Validate multiple emails in a single OData query."""
    # Build OData filter with IN clause
    emails_upper = [email.upper() for email in emails]
    email_list = "','".join(emails_upper)
    filter_clause = f"InternetEmailAddress in ('{email_list}')"

    # Query API
    response = await odata_client.query(
        filter=filter_clause,
        select="InternetEmailAddress,StatusCode,TerminationDate"
    )

    # Build result map
    results = {}
    found_emails = set()

    for employee in response["value"]:
        email = employee["InternetEmailAddress"].lower()
        found_emails.add(email)
        is_valid = (
            employee.get("StatusCode") == "3" and
            employee.get("TerminationDate") is None
        )
        results[email] = is_valid

    # Mark not found emails as invalid
    for email in emails:
        if email.lower() not in found_emails:
            results[email.lower()] = False

    return results
```

**Performance Notes:**
- Recommended batch size: 20 emails per request (avoid URL length limits)
- URL length limit: ~2000 characters (depends on server config)
- For larger batches, split into multiple requests

---

### 3. Get Employee Details (for manager lookup)

**Purpose**: Retrieve full employee details including manager information.

**Query:**
```
GET /workforce_fastapi/GWF_Workers?$filter=InternetEmailAddress eq 'CRODENAS@LILLY.COM'
```

**Request (Full Record):**
```http
GET /workforce_fastapi/GWF_Workers?$filter=SystemLogonId eq 'V5X1868' HTTP/1.1
Host: gateway-intranet.apim.lilly.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6...
Accept: application/json
```

**Response:** (Full employee record with 170+ fields - see example data above)

**Manager Escalation Fields:**
- `SupervisorEmail` - Manager's email for escalation
- `SupervisorGlobalId` - Manager's GlobalId for lookups
- `SupervisorFirstName` - Manager's first name
- `SupervisorLastName` - Manager's last name
- `SupervisorSystemId` - Manager's network ID

---

## Validation Rules

### Determining if an Employee is "Active"

An employee is considered **valid/active** if **ALL** of the following are true:

1. **Record exists**: `@odata.count >= 1`
2. **Status is Active**: `StatusCode == "3"` (Active)
3. **Not terminated**: `TerminationDate == null`
4. **Optional: Employee group**: `GroupCode == "A"` (Employee, not contractor)

**Python Implementation:**
```python
from datetime import datetime
from typing import Optional

class EmployeeStatus:
    """Employee validation status."""
    ACTIVE = "3"
    INACTIVE = "0"
    # Add other status codes as discovered

def is_valid_contact(employee_data: dict) -> tuple[bool, Optional[str]]:
    """
    Check if employee is a valid contact.

    Returns:
        tuple: (is_valid, reason_if_invalid)
    """
    if not employee_data:
        return False, "not_found"

    status_code = employee_data.get("StatusCode")
    if status_code != EmployeeStatus.ACTIVE:
        return False, f"inactive_status_{status_code}"

    termination_date = employee_data.get("TerminationDate")
    if termination_date is not None:
        return False, "terminated"

    # Optional: Check if employee (not contractor)
    group_code = employee_data.get("GroupCode")
    if group_code and group_code != "A":
        return False, f"non_employee_group_{group_code}"

    return True, None
```

---

## Email Address Normalization

**Important:** The API stores emails in **UPPERCASE** (`"CRODENAS@LILLY.COM"`), but queries should handle both cases.

**Normalization Strategy:**
```python
def normalize_email(email: str) -> str:
    """Normalize email for API queries."""
    # API stores uppercase, but OData filters are case-insensitive
    return email.upper()

# Query example
query_email = normalize_email("crodenas@lilly.com")  # -> "CRODENAS@LILLY.COM"
filter_clause = f"InternetEmailAddress eq '{query_email}'"
```

**Case Sensitivity:**
- OData `eq` operator: **Case-insensitive** (typically)
- Recommend: Uppercase emails in queries for consistency
- Response: Emails returned in uppercase, normalize to lowercase for ECHO

---

## OAuth2 Authentication Flow

### 1. Token Request

**Endpoint:**
```
POST https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token
```

**Request:**
```http
POST /oauth2/v2.0/token HTTP/1.1
Host: login.microsoftonline.com
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id={client_id}
&client_secret={client_secret}
&scope=api://gateway-intranet/.default
```

**Response (200 OK):**
```json
{
  "token_type": "Bearer",
  "expires_in": 3599,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6..."
}
```

### 2. Using Access Token

All API requests must include the access token in the Authorization header:

```http
GET /employees/validate HTTP/1.1
Host: gateway-intranet.apim.lilly.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsIng1dCI6...
Content-Type: application/json
```

### 3. Token Refresh

Tokens expire after ~1 hour (3599 seconds). ECHO must:
1. Cache the token with expiration time
2. Refresh proactively before expiration (e.g., 5 minutes before)
3. Handle 401 responses by refreshing token and retrying request

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | ECHO Action |
|------|---------|-------------|
| 200 | Success | Process response |
| 400 | Bad request (invalid email format) | Log error, mark contact as invalid |
| 401 | Unauthorized (token expired/invalid) | Refresh token and retry once |
| 403 | Forbidden (insufficient permissions) | Alert admin, disable contact validation |
| 404 | Employee not found | Mark contact as invalid |
| 429 | Rate limit exceeded | Exponential backoff, retry after delay |
| 500 | Internal server error | Retry with exponential backoff (3 attempts) |
| 503 | Service unavailable | Retry with exponential backoff (3 attempts) |

### Retry Strategy

```python
async def validate_email_with_retry(email: str, max_retries: int = 3) -> bool:
    """Validate email with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            response = await employee_api.validate_email(email)
            return response["is_valid"]
        except TokenExpiredError:
            await employee_api.refresh_token()
            continue  # Retry immediately after token refresh
        except RateLimitError as e:
            delay = 2 ** attempt  # 1s, 2s, 4s
            await asyncio.sleep(delay)
            continue
        except ServiceUnavailableError as e:
            if attempt == max_retries - 1:
                log.error("Employee API unavailable after retries", email=email)
                return False  # Assume invalid if API is down
            delay = 2 ** attempt
            await asyncio.sleep(delay)
            continue
        except Exception as e:
            log.error("Unexpected error validating email", email=email, error=str(e))
            return False  # Assume invalid on unexpected errors
    return False
```

---

## ECHO Configuration

### Secrets Manager Storage

Store credentials in AWS Secrets Manager:

```json
{
  "name": "echo/employee-api/prod",
  "secret": {
    "client_id": "12345678-1234-1234-1234-123456789012",
    "client_secret": "super-secret-value-here",
    "tenant_id": "87654321-4321-4321-4321-210987654321",
    "token_endpoint": "https://login.microsoftonline.com/87654321-4321-4321-4321-210987654321/oauth2/v2.0/token",
    "scope": "api://gateway-intranet/.default"
  }
}
```

### ECHO Settings (settings.py)

```python
class EmployeeAPISettings(BaseSettings):
    """Employee Directory OData API configuration."""
    model_config = SettingsConfigDict(env_prefix="EMPLOYEE_API_")

    enabled: bool = True
    environment: str = "prod"  # or "dev"

    # Endpoints (OData API)
    dev_base_url: str = "https://gateway-intranet.apim-dev.lilly.com/workforce_fastapi/GWF_Workers"
    prod_base_url: str = "https://gateway-intranet.apim.lilly.com/workforce_fastapi/GWF_Workers"

    # Credentials reference
    credentials_secret_arn: str = "arn:aws:secretsmanager:us-east-1:...:secret:echo/employee-api/prod"

    # Performance tuning
    batch_size: int = 20  # Max emails per OData IN query (URL length limit)
    cache_ttl: int = 3600  # Cache validation results for 1 hour
    rate_limit: int = 100  # Max requests per minute
    request_timeout: int = 30  # Timeout in seconds
    max_retries: int = 3

    # OData-specific settings
    odata_select_fields: str = "GlobalId,InternetEmailAddress,StatusCode,StatusDescription,TerminationDate,SupervisorEmail,FirstName,LastName,FriendlyFirstName,FriendlyLastName"

    @property
    def base_url(self) -> str:
        """Get base URL for current environment."""
        return self.dev_base_url if self.environment == "dev" else self.prod_base_url

class Settings(BaseSettings):
    """Main application settings."""
    # ... other settings ...
    employee_api: EmployeeAPISettings = EmployeeAPISettings()
```

### Environment Variables

```bash
# Employee API configuration (OData)
EMPLOYEE_API_ENABLED=true
EMPLOYEE_API_ENVIRONMENT=prod  # or dev
EMPLOYEE_API_CREDENTIALS_SECRET_ARN=arn:aws:secretsmanager:us-east-1:...:secret:echo/employee-api/prod
EMPLOYEE_API_BATCH_SIZE=20  # Lower for OData URL length limits
EMPLOYEE_API_CACHE_TTL=3600
EMPLOYEE_API_RATE_LIMIT=100
EMPLOYEE_API_REQUEST_TIMEOUT=30
EMPLOYEE_API_MAX_RETRIES=3
```

---

## OData Client Implementation

### Python OData Client

```python
from typing import Optional
import httpx
from datetime import datetime, timedelta
import structlog

log = structlog.get_logger(__name__)

class EmployeeODataClient:
    """Client for Employee Directory OData API with OAuth2 authentication."""

    def __init__(
        self,
        base_url: str,
        credentials: dict,
        cache_ttl: int = 3600,
        timeout: int = 30,
    ):
        self.base_url = base_url
        self.credentials = credentials
        self.cache_ttl = cache_ttl
        self.timeout = timeout

        self.http_client = httpx.AsyncClient(timeout=timeout)
        self.token_cache: Optional[dict] = None
        self.validation_cache: dict[str, tuple[bool, datetime]] = {}

    async def get_access_token(self) -> str:
        """Get cached OAuth2 token or request a new one."""
        # Check cache
        if self.token_cache:
            expires_at = self.token_cache.get("expires_at")
            if expires_at and datetime.utcnow() < expires_at:
                return self.token_cache["access_token"]

        # Request new token
        log.info("Requesting new OAuth2 access token")
        token_response = await self.http_client.post(
            self.credentials["token_endpoint"],
            data={
                "grant_type": "client_credentials",
                "client_id": self.credentials["client_id"],
                "client_secret": self.credentials["client_secret"],
                "scope": self.credentials["scope"],
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        token_response.raise_for_status()
        token_data = token_response.json()

        # Cache token with expiration (refresh 5 min early)
        expires_in = token_data.get("expires_in", 3599)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)

        self.token_cache = {
            "access_token": token_data["access_token"],
            "expires_at": expires_at,
        }

        log.info("OAuth2 token acquired", expires_at=expires_at.isoformat())
        return token_data["access_token"]

    async def query_odata(
        self,
        filter_clause: str,
        select_fields: Optional[str] = None,
        top: int = 100,
    ) -> dict:
        """Execute OData query against employee API."""
        token = await self.get_access_token()

        # Build query parameters
        params = {"$filter": filter_clause}
        if select_fields:
            params["$select"] = select_fields
        if top:
            params["$top"] = top

        # Execute request
        log.debug("Executing OData query", filter=filter_clause)
        response = await self.http_client.get(
            self.base_url,
            params=params,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()
        return response.json()

    async def validate_email(self, email: str) -> bool:
        """
        Check if email belongs to an active employee.

        Returns:
            bool: True if employee is active, False otherwise
        """
        # Check cache
        email_lower = email.lower()
        cached = self.validation_cache.get(email_lower)
        if cached:
            is_valid, cached_at = cached
            if datetime.utcnow() - cached_at < timedelta(seconds=self.cache_ttl):
                log.debug("Validation cache hit", email=email_lower)
                return is_valid

        # Query API
        email_upper = email.upper()
        filter_clause = f"InternetEmailAddress eq '{email_upper}'"
        select_fields = "GlobalId,InternetEmailAddress,StatusCode,StatusDescription,TerminationDate"

        try:
            result = await self.query_odata(
                filter_clause=filter_clause,
                select_fields=select_fields,
                top=1,
            )

            # Validate employee
            is_valid = False
            if result.get("@odata.count", 0) > 0:
                employee = result["value"][0]
                is_valid = (
                    employee.get("StatusCode") == "3"
                    and employee.get("TerminationDate") is None
                )

            # Cache result
            self.validation_cache[email_lower] = (is_valid, datetime.utcnow())

            log.info(
                "Email validation complete",
                email=email_lower,
                is_valid=is_valid,
            )
            return is_valid

        except httpx.HTTPStatusError as e:
            log.error(
                "Employee API error",
                email=email_lower,
                status_code=e.response.status_code,
                error=str(e),
            )
            return False  # Assume invalid on API error

    async def validate_emails_batch(self, emails: list[str]) -> dict[str, bool]:
        """
        Validate multiple emails in a single OData query.

        Args:
            emails: List of email addresses to validate (max 20)

        Returns:
            dict: {email: is_valid} mapping
        """
        if len(emails) > 20:
            raise ValueError("Batch size limited to 20 emails (URL length constraint)")

        # Check cache first
        results = {}
        uncached_emails = []

        for email in emails:
            email_lower = email.lower()
            cached = self.validation_cache.get(email_lower)
            if cached:
                is_valid, cached_at = cached
                if datetime.utcnow() - cached_at < timedelta(seconds=self.cache_ttl):
                    results[email_lower] = is_valid
                    continue
            uncached_emails.append(email)

        # Query API for uncached emails
        if uncached_emails:
            emails_upper = [e.upper() for e in uncached_emails]
            email_list = "','".join(emails_upper)
            filter_clause = f"InternetEmailAddress in ('{email_list}')"
            select_fields = "InternetEmailAddress,StatusCode,TerminationDate"

            try:
                result = await self.query_odata(
                    filter_clause=filter_clause,
                    select_fields=select_fields,
                    top=len(uncached_emails),
                )

                # Process results
                found_emails = set()
                for employee in result.get("value", []):
                    email_lower = employee["InternetEmailAddress"].lower()
                    found_emails.add(email_lower)

                    is_valid = (
                        employee.get("StatusCode") == "3"
                        and employee.get("TerminationDate") is None
                    )

                    results[email_lower] = is_valid
                    self.validation_cache[email_lower] = (is_valid, datetime.utcnow())

                # Mark not found as invalid
                for email in uncached_emails:
                    email_lower = email.lower()
                    if email_lower not in found_emails:
                        results[email_lower] = False
                        self.validation_cache[email_lower] = (False, datetime.utcnow())

                log.info(
                    "Batch validation complete",
                    total=len(emails),
                    valid=sum(results.values()),
                    invalid=len(results) - sum(results.values()),
                )

            except httpx.HTTPStatusError as e:
                log.error("Batch validation failed", error=str(e))
                # Mark all as invalid on error
                for email in uncached_emails:
                    results[email.lower()] = False

        return results

    async def get_employee_details(self, email: str) -> Optional[dict]:
        """
        Get full employee details including manager information.

        Returns:
            dict: Employee record or None if not found
        """
        email_upper = email.upper()
        filter_clause = f"InternetEmailAddress eq '{email_upper}'"

        try:
            result = await self.query_odata(filter_clause=filter_clause, top=1)

            if result.get("@odata.count", 0) == 0:
                return None

            return result["value"][0]

        except httpx.HTTPStatusError:
            return None

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
```

---

## Implementation Checklist

### Phase 1: Basic Integration
- [ ] Create `EmployeeAPIClient` class with OAuth2 support
- [ ] Implement token caching and automatic refresh
- [ ] Implement single email validation endpoint
- [ ] Add retry logic with exponential backoff
- [ ] Store credentials in AWS Secrets Manager
- [ ] Add health check endpoint for API connectivity

### Phase 2: Performance Optimization
- [ ] Implement batch validation endpoint
- [ ] Add validation result caching (1 hour TTL)
- [ ] Implement rate limiting (100 req/min)
- [ ] Add metrics and logging for API calls
- [ ] Monitor token refresh success rate

### Phase 3: Resilience
- [ ] Handle API downtime gracefully (fallback behavior)
- [ ] Add circuit breaker pattern (fail fast after N failures)
- [ ] Alert on sustained API failures
- [ ] Add API response time monitoring
- [ ] Implement request queuing for rate limit management

### Phase 4: Enhanced Features (Post-MVP)
- [ ] Cache employee details for manager lookup
- [ ] Support manager escalation using API data
- [ ] Track employee status changes over time
- [ ] Add bulk employee sync for offline validation

---

## Testing Strategy

### Unit Tests
```python
@pytest.fixture
def mock_employee_api():
    """Mock employee API responses."""
    return AsyncMock()

async def test_validate_email_returns_true_for_valid_employee(mock_employee_api):
    """Test that valid employee email returns true."""
    mock_employee_api.validate_email.return_value = {"is_valid": True}

    client = EmployeeAPIClient(mock_employee_api)
    result = await client.validate_email("alice@lilly.com")

    assert result is True
    mock_employee_api.validate_email.assert_called_once_with("alice@lilly.com")

async def test_validate_email_retries_on_token_expiration(mock_employee_api):
    """Test that token refresh triggers retry."""
    mock_employee_api.validate_email.side_effect = [
        TokenExpiredError(),
        {"is_valid": True}
    ]

    client = EmployeeAPIClient(mock_employee_api)
    result = await client.validate_email("alice@lilly.com")

    assert result is True
    assert mock_employee_api.refresh_token.called
```

### Integration Tests
- Test against dev environment with real OAuth2 flow
- Validate token caching and refresh
- Test batch validation with 100+ emails
- Verify rate limiting behavior
- Test API downtime scenarios

### Load Tests
- Validate 1000+ emails in parallel (batch processing)
- Measure token refresh performance under load
- Test rate limit handling with concurrent requests
- Verify cache hit rates

---

## Monitoring and Alerting

### Metrics to Track
- **API call success rate** (target: >99.5%)
- **API response time** (p50, p95, p99)
- **Token refresh success rate** (target: 100%)
- **Cache hit rate** (target: >80%)
- **Rate limit hits** (should be 0 with proper backoff)
- **Validation result distribution** (% valid vs invalid)

### Alerts
- **Critical**: Employee API unavailable for >5 minutes
- **Critical**: Token refresh failures (3+ consecutive failures)
- **Warning**: API response time >5s (p95)
- **Warning**: Cache hit rate <70%
- **Info**: Rate limit exceeded (review batch size/timing)

---

## Security Considerations

1. **Credential Storage**: Always use AWS Secrets Manager, never environment variables
2. **Token Security**: Never log access tokens
3. **TLS/HTTPS**: All API calls over HTTPS only
4. **Least Privilege**: Request minimum necessary scopes
5. **Rotation**: Rotate client secrets every 90 days
6. **Audit Logging**: Log all validation attempts (email + result + timestamp)
7. **PII Protection**: Never cache full employee details (only validation results)

---

## API Contract Questions for Employee API Team

Before implementation, clarify with the Employee API team:

1. **✅ API Type**: Confirmed OData v4 (`/workforce_fastapi/GWF_Workers`)
2. **✅ Base URLs**: Dev and Prod endpoints confirmed
3. **Rate limits**: What are the actual rate limits per client_id? (need to confirm)
4. **OData capabilities**:
   - Does the API support `$filter` with `in` operator? (for batch validation)
   - Max URL length for filter clauses?
   - Does `$count` work? (for checking existence)
5. **Status codes**: What are all possible `StatusCode` values besides "3" (Active) and "0" (Inactive)?
6. **Group codes**: What are all possible `GroupCode` values? (A=Employee, what about contractors?)
7. **Email case sensitivity**: Confirm OData `eq` operator is case-insensitive for email lookups
8. **Scope naming**: Confirm exact OAuth2 scope name (`api://gateway-intranet/.default`)
9. **SLA**: What's the API availability SLA? (for circuit breaker tuning)
10. **Maintenance windows**: Are there scheduled maintenance windows to avoid?
11. **Test credentials**: Can we get test `client_id`/`client_secret` for dev environment?
12. **Manager escalation**:
    - Is `SupervisorEmail` always populated for active employees?
    - What if manager is also terminated - should ECHO walk up the chain?
13. **Pagination**: Does the API support `$skip` and `$top` for large result sets?
14. **Performance**: Expected response time for single query? Batch of 20?

---

## Additional Implementation Notes

### Manager Escalation Support

ECHO can use `SupervisorEmail` field for automatic manager escalation:

**Escalation Rule Example:**
```json
{
  "escalation_rules": [
    {"level": 0, "recipients": ["owner"], "delay_days": 0},
    {"level": 1, "recipients": ["owner", "owner.manager"], "delay_days": 7}
  ]
}
```

**Implementation:**
```python
async def resolve_manager_email(employee_email: str, client: EmployeeODataClient) -> Optional[str]:
    """Get manager email for an employee."""
    employee = await client.get_employee_details(employee_email)
    if employee:
        return employee.get("SupervisorEmail")
    return None
```

### Contractor Handling

**Question**: Should contractors be considered valid contacts?

- `GroupCode == "A"` → Employee
- `GroupCode == "C"` (?) → Contractor

**Options:**
1. **Include contractors**: Validate `StatusCode == "3"` only (ignore group)
2. **Exclude contractors**: Validate `StatusCode == "3"` AND `GroupCode == "A"`
3. **Configurable**: Campaign-level setting for whether to include contractors

**Recommendation**: Start with Option 1 (include contractors), add filter option post-MVP if needed.

---
