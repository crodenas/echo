# Schedule UX Improvements

**Date**: 2026-01-23
**Status**: Proposal - Not yet implemented

## Problem Statement

Users currently must manually enter AWS cron expressions (e.g., `cron(*/45 * * * ? *)`) directly into text fields when creating or updating campaigns. This creates several issues:

1. **Complex syntax**: AWS cron format differs from standard Unix cron (requires `?` wildcards, uses `cron()` wrapper)
2. **Error-prone**: Easy to make syntax mistakes with no validation
3. **Poor UX**: No guidance, no preview of when schedules will actually run
4. **Accessibility**: Requires technical knowledge of cron expressions

## Current Implementation

**Files affected**:
- `src/core/models.py`: Lines 12-13, 23-24 (campaign_schedule and cycle_schedule as plain strings)
- `src/templates/create.html`: Lines 15-21 (text input fields with minimal help text)
- `src/templates/update.html`: Lines 17-23 (same pattern)
- `src/api/routes/basic.py`: Lines 32-33 (form fields)

**Current UX**:
```html
<label for="campaign_schedule">Campaign Schedule:</label>
<input type="text" name="campaign_schedule" value="cron(*/45 * * * ? *)" required>
<small>Every 45 minutes (cron format: minute hour day month day-of-week year)</small>
```

## Proposed Solutions

### Option 1: Schedule Builder UI (Recommended for most users)

Add a visual schedule builder with:
- Dropdown for frequency (Every X minutes/hours/days/weeks/months)
- Time picker for specific times
- Day-of-week checkboxes for weekly schedules
- Preview showing next 5 execution times
- "Advanced" toggle to switch to raw cron expression

**Pros**: User-friendly, catches errors early, accessible to non-technical users
**Cons**: More complex to build, limited to common patterns

### Option 2: Predefined Schedule Templates

Offer common presets as dropdown options:
- "Every 5 minutes" → `cron(*/5 * * * ? *)`
- "Every 15 minutes" → `cron(*/15 * * * ? *)`
- "Every hour" → `cron(0 * * * ? *)`
- "Daily at 9 AM" → `cron(0 9 * * ? *)`
- "Daily at midnight" → `cron(0 0 * * ? *)`
- "Weekly on Monday at 9 AM" → `cron(0 9 ? * MON *)`
- "Monthly on 1st at midnight" → `cron(0 0 1 * ? *)`
- "Custom" → Falls back to text input

**Pros**: Quick to implement, covers 80% of use cases, educates users
**Cons**: Limited flexibility for edge cases

### Option 3: Natural Language Input

Use a parser to convert natural language to cron:
- "every 5 minutes" → `cron(*/5 * * * ? *)`
- "daily at 9am" → `cron(0 9 * * ? *)`
- "every monday at 10:30" → `cron(30 10 ? * MON *)`

**Pros**: Intuitive, low learning curve
**Cons**: Parser complexity, ambiguity handling, dependency on parsing library

### Option 4: Hybrid Approach (Best overall)

Combine Options 1 + 2:
1. Show preset templates for common schedules
2. Provide visual builder for custom schedules
3. Allow "Expert mode" for direct cron input
4. Add real-time validation and next-run preview

**Pros**: Flexible, user-friendly, covers all use cases
**Cons**: Most complex to implement

## Implementation Recommendations

### Phase 1: Quick Win - Templates (Option 2)

**Backend changes**:

1. Create `src/utils/schedule_templates.py`:
```python
SCHEDULE_TEMPLATES = {
    "every_5_min": "cron(*/5 * * * ? *)",
    "every_15_min": "cron(*/15 * * * ? *)",
    "every_30_min": "cron(*/30 * * * ? *)",
    "every_hour": "cron(0 * * * ? *)",
    "daily_9am": "cron(0 9 * * ? *)",
    "daily_midnight": "cron(0 0 * * ? *)",
    "weekly_monday_9am": "cron(0 9 ? * MON *)",
    "monthly_1st_midnight": "cron(0 0 1 * ? *)",
}
```

2. Add validation utility in `src/utils/schedule_validation.py`:
```python
from aws_croniter import AWSCroniter
from datetime import datetime

def validate_aws_cron(expression: str) -> bool:
    """Validate AWS cron expression."""
    try:
        AWSCroniter(expression, datetime.now())
        return True
    except Exception:
        return False

def get_next_n_runs(expression: str, n: int = 5) -> list[datetime]:
    """Get next N execution times for a schedule."""
    cron = AWSCroniter(expression, datetime.now())
    return [cron.get_next(datetime) for _ in range(n)]
```

3. Add API endpoints in `src/api/routes/schedules.py`:
```python
@router.get("/templates")
async def get_schedule_templates():
    """Get available schedule templates."""
    return SCHEDULE_TEMPLATES

@router.get("/validate")
async def validate_schedule(cron: str):
    """Validate AWS cron expression and preview next runs."""
    is_valid = validate_aws_cron(cron)
    next_runs = get_next_n_runs(cron) if is_valid else []
    return {"valid": is_valid, "next_runs": next_runs}
```

**Frontend changes**:

Update `src/templates/create.html` and `src/templates/update.html`:
```html
<label for="campaign_schedule">Campaign Schedule:</label>
<select id="campaign_schedule_preset" onchange="updateCronField(this, 'campaign_schedule')">
    <option value="">-- Select Preset --</option>
    <option value="cron(*/5 * * * ? *)">Every 5 minutes</option>
    <option value="cron(*/15 * * * ? *)">Every 15 minutes</option>
    <option value="cron(0 * * * ? *)">Every hour</option>
    <option value="cron(0 9 * * ? *)">Daily at 9 AM</option>
    <option value="custom">Custom (enter below)</option>
</select>
<input type="text" id="campaign_schedule" name="campaign_schedule" required>
<div id="schedule_preview"></div>
```

### Phase 2: Enhanced UX - Builder UI (Option 4)

Add JavaScript-based schedule builder or consider a lightweight library like:
- `cron-builder` (if adapting for AWS cron format)
- Custom React/Vue component if moving to SPA

Add real-time preview using the validation API endpoint.

## Files to Modify

- `src/utils/schedule_templates.py` (new)
- `src/utils/schedule_validation.py` (new)
- `src/api/routes/schedules.py` (new)
- `src/templates/create.html` (update form)
- `src/templates/update.html` (update form)
- `src/core/models.py` (potentially add validation)
- Add JavaScript for dynamic UI behavior

## Testing Considerations

- Unit tests for schedule validation
- Unit tests for next-run calculations
- Integration tests for template API endpoints
- Manual UI testing for form interactions
- Edge case testing (invalid cron, timezone handling)

## Future Enhancements

- Timezone support (AWS EventBridge uses UTC by default)
- Schedule conflict detection (e.g., cycle_schedule faster than campaign_schedule)
- Visual timeline showing campaign and cycle execution patterns
- Import/export schedule configurations
- Schedule simulation/dry-run mode

## References

- AWS EventBridge Scheduler cron format: https://docs.aws.amazon.com/scheduler/latest/UserGuide/schedule-types.html#cron-based
- `aws-croniter` library: Already in use per `docs/Design.md`
- Current cron usage: `CLAUDE.md` line 82-87
