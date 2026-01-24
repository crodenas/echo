# Chain Scheduling Architecture Refactor

## Context

Current implementation pre-creates all cycle schedules when a campaign starts:
- Campaign schedule fires every 6 months → Queue 1
- Queue 1 creates N one-time cycle schedules (where N = max_events, e.g., 4)
- Each cycle schedule fires → Queue 2 → Execute cycle

**Problem**: This works but lacks flexibility for pause/resume, cancellation, and adaptation based on cycle results.

## Proposed Solution: Chain Scheduling

Instead of pre-creating all cycle schedules, create them one at a time:

```
Campaign Schedule (every 6 months, recurring)
  ↓
Queue 1: Reset cycle counter, create first cycle schedule (immediate)
  ↓
Queue 2:
  ├─ Execute cycle
  ├─ Increment current_cycle counter
  ├─ Check: current_cycle < max_events?
  └─ If yes: Create next cycle schedule (one-time, +2 weeks from now)

Repeats until current_cycle = max_events, then stops
```

## Benefits

1. **Flexibility**: Easy to cancel campaigns mid-flight (just don't create next schedule)
2. **Adaptability**: Can add logic like "stop early if error rate > threshold"
3. **Observability**: DB tracks current_cycle, last_cycle_at for visibility
4. **Scalability**: Works for any max_events without AWS quota concerns (only 1-2 schedules exist at a time)
5. **Resilience**: If a cycle fails, don't create the next one

## Implementation Steps

### 1. Database Schema Changes

Add fields to track campaign execution state:

```python
# db/schemas.py
class Campaign(Base):
    __tablename__ = "campaigns"

    # ... existing fields ...

    # NEW: Track execution state
    current_cycle: Mapped[int] = mapped_column(default=0)
    last_cycle_at: Mapped[datetime | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(default="scheduled")  # scheduled, running, completed, paused, failed
```

**Migration**: Create Alembic migration to add these fields.

### 2. Queue 1 Handler Changes

**Purpose**: When campaign starts (every 6 months), reset state and create first cycle.

```python
# core/queue_handlers.py
async def handle_queue_1_messages(sqs_client, queue_url: str):
    """Campaign start trigger - reset state and create first cycle schedule."""
    while True:
        response = await asyncio.to_thread(
            sqs_client.receive_message,
            QueueUrl=queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=20
        )

        for message in response.get('Messages', []):
            body = json.loads(message['Body'])
            campaign_id = body['campaign_id']

            # Reset campaign state for new run
            with sessionmaker(bind=echo_engine)() as session:
                campaign = session.query(Campaign).filter_by(id=campaign_id).first()

                if not campaign:
                    logger.error(f"Campaign {campaign_id} not found")
                    continue

                # Reset for new campaign run
                campaign.current_cycle = 0
                campaign.last_cycle_at = None
                campaign.status = "running"
                session.commit()

            # Create first cycle schedule (immediate execution)
            await create_first_cycle_schedule(campaign_id)

            logger.info(f"Campaign {campaign_id} started, first cycle scheduled")

            # Delete message from queue
            await asyncio.to_thread(
                sqs_client.delete_message,
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
```

### 3. Queue 2 Handler Changes

**Purpose**: Execute cycle AND create next cycle schedule if needed.

```python
# core/queue_handlers.py
async def handle_queue_2_messages(sqs_client, queue_url: str):
    """Execute cycle, then create next cycle schedule if not done."""
    while True:
        response = await asyncio.to_thread(
            sqs_client.receive_message,
            QueueUrl=queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=20
        )

        for message in response.get('Messages', []):
            body = json.loads(message['Body'])
            campaign_id = body['campaign_id']

            with sessionmaker(bind=echo_engine)() as session:
                campaign = session.query(Campaign).filter_by(id=campaign_id).first()

                if not campaign:
                    logger.error(f"Campaign {campaign_id} not found")
                    continue

                # Increment cycle counter
                campaign.current_cycle += 1
                current_cycle = campaign.current_cycle
                campaign.last_cycle_at = datetime.now(timezone.utc)

                logger.info(f"Executing campaign {campaign_id}, cycle {current_cycle}/{campaign.max_events}")

                try:
                    # TODO: Execute actual campaign cycle logic
                    # - Fetch data from campaign.conn_string
                    # - Send notifications
                    # - Record results

                    session.commit()

                    # Should we create the next cycle?
                    if current_cycle < campaign.max_events:
                        # Calculate next cycle time using aws-croniter
                        next_time = calculate_next_cycle_time(
                            campaign.cycle_schedule,
                            campaign.last_cycle_at
                        )

                        # Create one-time schedule for next cycle
                        await create_next_cycle_schedule(
                            campaign_id=campaign.id,
                            cycle_number=current_cycle + 1,
                            execution_time=next_time
                        )

                        logger.info(f"Campaign {campaign_id}: Scheduled cycle {current_cycle + 1} for {next_time}")
                    else:
                        # All cycles completed
                        campaign.status = "completed"
                        session.commit()
                        logger.info(f"Campaign {campaign_id} completed all {campaign.max_events} cycles")

                except Exception as e:
                    logger.error(f"Campaign {campaign_id} cycle {current_cycle} failed: {e}")
                    campaign.status = "failed"
                    session.commit()
                    # Don't create next cycle schedule on failure

            # Delete message from queue
            await asyncio.to_thread(
                sqs_client.delete_message,
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )
```

### 4. New Scheduler Functions

```python
# core/scheduler.py

async def create_first_cycle_schedule(campaign_id: int) -> None:
    """Create immediate one-time schedule for first cycle."""
    scheduler_client = get_scheduler_client()

    schedule_name = f"campaign_{campaign_id}_cycle_1_schedule"
    group_name = f"campaign_{campaign_id}_group"

    # Execute immediately (or with small delay, e.g., 1 minute from now)
    now = datetime.now(timezone.utc)
    start_time = now + timedelta(minutes=1)
    schedule_expression = f"at({start_time.strftime('%Y-%m-%dT%H:%M:%S')})"

    await asyncio.to_thread(
        scheduler_client.create_schedule,
        Name=schedule_name,
        GroupName=group_name,
        ScheduleExpression=schedule_expression,
        FlexibleTimeWindow={'Mode': 'OFF'},
        Target={
            'Arn': QUEUE_2_ARN,  # Goes directly to Queue 2
            'RoleArn': EXECUTION_ROLE_ARN,
            'Input': json.dumps({
                'campaign_id': campaign_id,
                'cycle_number': 1,
                'schedule_name': schedule_name
            }),
            'DeadLetterConfig': {'Arn': DEAD_LETTER_QUEUE_ARN}  # Optional
        },
        ActionAfterCompletion='DELETE'  # Auto-delete after execution
    )

    logger.info(f"Created first cycle schedule {schedule_name}")


async def create_next_cycle_schedule(
    campaign_id: int,
    cycle_number: int,
    execution_time: datetime
) -> None:
    """Create one-time schedule for next cycle at specified time."""
    scheduler_client = get_scheduler_client()

    schedule_name = f"campaign_{campaign_id}_cycle_{cycle_number}_schedule"
    group_name = f"campaign_{campaign_id}_group"

    schedule_expression = f"at({execution_time.strftime('%Y-%m-%dT%H:%M:%S')})"

    await asyncio.to_thread(
        scheduler_client.create_schedule,
        Name=schedule_name,
        GroupName=group_name,
        ScheduleExpression=schedule_expression,
        FlexibleTimeWindow={'Mode': 'OFF'},
        Target={
            'Arn': QUEUE_2_ARN,
            'RoleArn': EXECUTION_ROLE_ARN,
            'Input': json.dumps({
                'campaign_id': campaign_id,
                'cycle_number': cycle_number,
                'schedule_name': schedule_name
            })
        },
        ActionAfterCompletion='DELETE'
    )

    logger.info(f"Created cycle {cycle_number} schedule {schedule_name} for {execution_time}")


def calculate_next_cycle_time(cycle_schedule: str, from_time: datetime) -> datetime:
    """Calculate next execution time based on cycle_schedule cron expression."""
    from aws_croniter import AWSCroniter

    # cycle_schedule is in AWS cron format: "cron(0 12 ? * MON *)"
    # Extract the cron expression (remove "cron(...)")
    cron_expr = cycle_schedule.replace("cron(", "").replace(")", "")

    cron = AWSCroniter(cron_expr, from_time)
    next_time = cron.get_next(datetime)

    return next_time
```

### 5. Remove Old Code

Delete the `create_cycle_schedules()` function from `core/scheduler.py` - it's no longer needed.

### 6. Update Campaign Creation

```python
# services/campaigns.py
async def create_campaign(campaign_data: dict) -> Campaign:
    """Create campaign with initial state."""
    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = to_schema(Campaign(**campaign_data))

        # Set initial state
        campaign_model.current_cycle = 0
        campaign_model.status = "scheduled"

        session.add(campaign_model)
        session.flush()  # Get ID

        campaign = to_domain(campaign_model)

        try:
            # Create schedule group and main campaign schedule
            await create_schedule_group(campaign)
            await create_campaign_schedule(campaign)  # Recurring, every 6 months

            session.commit()
            return campaign
        except Exception:
            session.rollback()
            raise
```

## Testing Strategy

1. **Unit tests**: Test `calculate_next_cycle_time()` with various cron expressions
2. **Integration tests**: Mock SQS/EventBridge, verify state transitions
3. **Manual testing**:
   - Create campaign with max_events=2, cycle_schedule="cron(* * * * ? *)" (every minute)
   - Verify: First cycle executes, second cycle scheduled, then stops

## Migration Path

1. Add DB fields (migration)
2. Update Queue 1 handler (backward compatible - old campaigns still work)
3. Update Queue 2 handler (add chain scheduling logic)
4. Deploy to dev environment
5. Test with new campaign
6. Once validated, new campaigns use chain scheduling

**Note**: Existing campaigns with pre-created schedules will complete normally. New campaigns will use chain scheduling.

## Future Enhancements

With this architecture, you can easily add:

- **Pause/Resume**: Set status='paused', next cycle won't be created
- **Early termination**: "Stop if 90% response rate achieved"
- **Adaptive timing**: "If cycle fails, retry in 1 day instead of 2 weeks"
- **Manual cycle trigger**: API endpoint to create next cycle schedule immediately
- **Campaign extension**: Increase max_events mid-flight

## Rollback Plan

If chain scheduling has issues:
1. Revert Queue 2 handler changes
2. Recreate `create_cycle_schedules()` function
3. Update Queue 1 to call it again
4. DB fields (current_cycle, status) can remain unused
