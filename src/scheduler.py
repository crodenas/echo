"""
Scheduler utilities for creating one-time schedules.
"""

import json
from datetime import datetime

import config
from aws.scheduler import create_schedule

TARGET_ARN: str = config.TARGET_ARN
EXECUTION_ROLE_ARN: str = config.EXECUTION_ROLE_ARN


def create_one_time_schedule(
    run_datetime: datetime,
    schedule_name: str,
    target_arn: str = TARGET_ARN,
    role_arn: str = EXECUTION_ROLE_ARN,
    group_name: str = None,
    description: str = None,
) -> str:
    """
    Create a one-time EventBridge Scheduler schedule for the given datetime.

    Args:
        run_datetime: The datetime when the schedule should run (in UTC).
        target_arn: The ARN of the target (e.g., Lambda function ARN).
        role_arn: The ARN of the IAM role for EventBridge Scheduler.
        schedule_name: Unique name for the schedule.
        group_name: Optional schedule group name.
        description: Optional description for the schedule.

    Returns:
        The ARN of the created schedule.
    """
    # Format datetime to ISO 8601 string for the 'at()' expression
    # EventBridge Scheduler expects UTC time
    schedule_expression = f"at({run_datetime.strftime('%Y-%m-%dT%H:%M:%S')})"

    # For one-time schedules, flexible time window is OFF
    flexible_time_window = {"Mode": "OFF"}

    # Create the target configuration
    target = {
        "Arn": target_arn,
        "Input": json.dumps({"MessageBody": "Hello from EventBridge Scheduler!"}),
        "RoleArn": role_arn,
    }

    # Create the schedule
    response = create_schedule(
        name=schedule_name,
        schedule_expression=schedule_expression,
        flexible_time_window=flexible_time_window,
        target=target,
        group_name=group_name,
        description=description,
        state="ENABLED",
    )

    return response.schedule_arn
