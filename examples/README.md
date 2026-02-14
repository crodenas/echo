# ECHO Examples

This directory contains example data and sample configurations for ECHO.

## Data Files

- **Employees.json** - Sample employee directory (~1000 employees)
- **Reviewables1.json** - Example reviewable resources for campaign 1
- **Reviewables2.json** - Example reviewable resources for campaign 2

## Usage

These files demonstrate the expected data format for external data sources that ECHO integrates with (read-only).

## Employee Data Structure

The `Employees.json` file represents the Azure AD protected Employee API that ECHO uses for contact resolution and manager hierarchy.

### Key Fields

```json
{
  "SystemId": "j2y0092",              // Unique employee identifier
  "GlobalId": 220,                     // Global employee number
  "FirstName": "Rosita",
  "LastName": "Kingstne",
  "InternetEmailAddress": "rkingstne63@creativecommons.org",
  "JobTitle": "Director of Engineering",
  "SupervisorSystemId": "q8r3249"     // Manager's SystemId (null for CEO)
}
```

### How ECHO Uses This Data

1. **Contact Resolution**: Data sources reference employees by `SystemId`:
   ```json
   {
     "object_id": "service-123",
     "tech_lead": "j2y0092",        // SystemId → resolves to Rosita
     "product_owner": "o2t9772"     // SystemId → resolves to Jemie
   }
   ```

2. **Manager Hierarchy**: The `SupervisorSystemId` field enables manager escalations:
   - Rosita (`j2y0092`) → manager is Cortney (`q8r3249`, CEO)
   - Escalation recipients `["tech_lead", "tech_lead.manager"]` resolves to:
     - Rosita Kingstne (tech_lead)
     - Cortney Larner (tech_lead's manager)

3. **Organizational Structure**:
   - **CEO**: Cortney Larner (`q8r3249`) - `SupervisorSystemId: null`
   - **Directors**: Report to CEO (Engineering, Sales, Marketing, HR)
   - **Managers**: Report to Directors
   - **Individual Contributors**: Report to Managers

### Example Hierarchy Traversal

```python
# Get employee and their manager
employee = get_employee("j2y0092")          # Rosita Kingstne
manager = get_employee(employee.SupervisorSystemId)  # Cortney Larner

# Multi-level escalation
# Start: Rosita (j2y0092)
# → Manager: Cortney (q8r3249, CEO)
# → Manager's Manager: None (Cortney is top of hierarchy)
```

See `docs/decisions.md` (Decision #13) for complete integration details.
