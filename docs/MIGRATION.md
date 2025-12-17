# Migration Guide: New Project Structure

This guide documents the changes made to improve Echo's project structure.

## Summary of Changes

### 1. New Directory Structure
- ✅ Added `tests/` for test suite with pytest configuration
- ✅ Added `examples/` for sample data (moved from `src/data/`)
- ✅ Added `scripts/` for utility scripts
- ✅ Added `src/services/` for service layer
- ✅ Removed duplicate `templates/` at root (kept in `src/templates/`)

### 2. Service Layer Introduction
**New:** `src/services/campaign_service.py`
- Centralizes all campaign business logic
- Coordinates between domain models, database, and AWS scheduler
- Proper transaction management
- Better separation of concerns

**Deprecated:** `src/core/campaign.py`
- Functions moved to `services/campaign_service.py`
- Keep for reference but use service layer going forward

### 3. Import Changes

**Before:**
```python
from core import campaign as lib_campaign
result = await lib_campaign.create_campaign(campaign)
```

**After:**
```python
from services import campaign_service
result = await campaign_service.create_campaign(campaign)
```

### 4. Package Organization
All `__init__.py` files now have:
- Proper docstrings explaining package purpose
- Explicit exports via `__all__`
- Better discoverability

### 5. Configuration Updates
- `pyproject.toml` now includes test dependencies (pytest, httpx)
- Added pytest configuration
- Updated `isort` to recognize new `services` package
- Added build system configuration

### 6. Data File Location
**Before:** `src/data/Employees.json`
**After:** `examples/data/Employees.json`

Updated in:
- `src/core/employees.py` → `DB_FILE = "examples/data/Employees.json"`

### 7. Templates Path
**Before:** `templates = Jinja2Templates(directory="templates")`
**After:** `templates = Jinja2Templates(directory="src/templates")`

Updated in:
- `src/api/routes/basic.py`

## Migration Checklist

If you have custom code or branches, update:

- [ ] Change imports from `core.campaign` to `services.campaign_service`
- [ ] Update template directory references to `src/templates`
- [ ] Move any custom data files to `examples/data/`
- [ ] Update test imports to use new service layer
- [ ] Install new dev dependencies: `uv sync`

## New Project Structure

```
echo/
├── docs/                    # Documentation
├── examples/                # Sample data (NEW)
│   └── data/
├── scripts/                 # Utility scripts (NEW)
├── src/
│   ├── api/                # HTTP routes
│   ├── core/               # Domain models & utilities
│   ├── db/                 # Database layer
│   ├── services/           # Business logic (NEW)
│   ├── templates/          # Jinja2 templates
│   ├── utils/              # Utilities
│   └── main.py
├── tests/                  # Test suite (NEW)
└── pyproject.toml
```

## Running After Migration

```bash
# Install dependencies (including new test deps)
uv sync

# Run application (no changes needed)
uv run fastapi dev src/main.py

# Run tests (new capability)
uv run pytest

# Run with watching for changes
uv run pytest --watch
```

## Benefits

### 1. Better Separation of Concerns
- **API Layer** - HTTP only
- **Service Layer** - Business logic
- **Core Layer** - Domain models
- **DB Layer** - Persistence

### 2. Improved Testability
- Service layer is easily mockable
- Test infrastructure in place
- Example fixtures provided

### 3. Clearer Dependencies
- Explicit imports via `__all__`
- Service layer as single entry point
- No circular dependencies

### 4. Standard Python Layout
- Follows Python best practices
- Familiar to Python developers
- Better IDE support

### 5. Future-Ready
- Repository pattern can be added
- Dependency injection ready
- Microservice extraction possible

## Backward Compatibility

The old `core/campaign.py` still exists but is deprecated. Update your code to use the new service layer:

```python
# Old (still works but deprecated)
from core import campaign as lib_campaign
await lib_campaign.create_campaign(campaign)

# New (preferred)
from services import campaign_service
await campaign_service.create_campaign(campaign)
```

## Questions?

See [docs/project_structure.md](project_structure.md) for detailed architecture documentation.
