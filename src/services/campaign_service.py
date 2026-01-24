"""Campaign service module.

Handles all campaign-related business logic including CRUD operations
and coordination with AWS EventBridge scheduler.
"""

from typing import List

from sqlalchemy.orm import sessionmaker

from core.exceptions import (
    CampaignNotFoundError,
    DatabaseError,
    ScheduleGroupAlreadyExistsError,
    ScheduleGroupNotFoundError,
    SchedulerError,
)
from core.logger import get_logger
from core.models import Campaign
from core.scheduler import (
    create_campaign_schedule,
    create_schedule_group,
    delete_schedule_group,
    list_schedules,
    update_campaign_schedule,
)
from db.db_engine import echo_engine
from db.schemas import CampaignSchema

logger = get_logger(__name__)


async def create_campaign(campaign: Campaign) -> Campaign:
    """Create a new campaign with associated AWS EventBridge schedules.

    This function performs the following steps in a coordinated transaction:
    1. Insert campaign into database (flush to get ID)
    2. Create AWS EventBridge schedule group
    3. Create AWS EventBridge campaign schedule
    4. Commit database transaction only if AWS operations succeed

    Args:
        campaign: Campaign domain model to create

    Returns:
        Created campaign with generated ID

    Raises:
        SchedulerError: If AWS schedule creation fails
        DatabaseError: If database operation fails
    """
    logger.info(
        f"Creating campaign: {campaign.name}",
        extra={"campaign_name": campaign.name},
    )

    with sessionmaker(bind=echo_engine)() as session:
        try:
            # Step 1: Add to database and flush to get ID
            campaign_model = to_schema(campaign)
            session.add(campaign_model)
            session.flush()  # Assign ID without committing

            # Update campaign with the generated ID
            new_campaign = to_domain(campaign_model)

            logger.debug(
                f"Campaign {new_campaign.name} added to session with ID {new_campaign.id}",
                extra={"campaign_id": new_campaign.id, "campaign_name": new_campaign.name},
            )

        except Exception as e:
            session.rollback()
            logger.error(
                f"Database error creating campaign {campaign.name}",
                extra={
                    "campaign_name": campaign.name,
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
            )
            raise DatabaseError(
                f"Failed to create campaign in database: {campaign.name}",
                context={"campaign_name": campaign.name},
                original_error=e,
            ) from e

        # Step 2 & 3: Create AWS resources
        try:
            # Create schedule group
            try:
                await create_schedule_group(campaign=new_campaign)
            except ScheduleGroupAlreadyExistsError:
                # Idempotent - group already exists is OK
                logger.info(
                    f"Schedule group already exists for campaign {new_campaign.id}",
                    extra={"campaign_id": new_campaign.id},
                )

            # Create campaign schedule
            await create_campaign_schedule(campaign=new_campaign)

            # Step 4: Commit only after AWS operations succeed
            session.commit()

            logger.info(
                f"Successfully created campaign {new_campaign.id}: {new_campaign.name}",
                extra={"campaign_id": new_campaign.id, "campaign_name": new_campaign.name},
            )

            return new_campaign

        except SchedulerError as e:
            session.rollback()
            logger.error(
                f"AWS scheduler error creating campaign {new_campaign.id}",
                extra={
                    "campaign_id": new_campaign.id,
                    "campaign_name": new_campaign.name,
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
            )
            raise  # Re-raise scheduler error for API layer
        except Exception as e:
            session.rollback()
            logger.error(
                f"Unexpected error creating campaign {new_campaign.id}",
                extra={
                    "campaign_id": new_campaign.id,
                    "campaign_name": new_campaign.name,
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
            )
            raise SchedulerError(
                f"Unexpected error creating AWS schedules for campaign {new_campaign.id}",
                context={"campaign_id": new_campaign.id},
                original_error=e,
            ) from e


async def update_campaign(campaign: Campaign) -> Campaign | None:
    """Update an existing campaign and its AWS EventBridge schedules.

    Args:
        campaign: Campaign domain model with updated data

    Returns:
        Updated campaign or None if not found

    Raises:
        SchedulerError: If AWS schedule update fails
        DatabaseError: If database operation fails
        CampaignNotFoundError: If campaign doesn't exist
    """
    logger.info(
        f"Updating campaign {campaign.id}",
        extra={"campaign_id": campaign.id, "campaign_name": campaign.name},
    )

    with sessionmaker(bind=echo_engine)() as session:
        # Check if campaign exists
        existing = session.get(CampaignSchema, campaign.id)
        if not existing:
            logger.warning(
                f"Campaign {campaign.id} not found for update",
                extra={"campaign_id": campaign.id},
            )
            raise CampaignNotFoundError(
                f"Campaign {campaign.id} not found",
                context={"campaign_id": campaign.id},
            )

        try:
            # Merge changes into session
            campaign_model = to_schema(campaign)
            session.merge(campaign_model)

            # Update AWS schedule
            try:
                await update_campaign_schedule(campaign=to_domain(campaign_model))
            except SchedulerError as e:
                session.rollback()
                logger.error(
                    f"AWS scheduler error updating campaign {campaign.id}",
                    extra={
                        "campaign_id": campaign.id,
                        "error_type": type(e).__name__,
                        "error": str(e),
                    },
                )
                raise

            # Commit database changes
            session.commit()

            logger.info(
                f"Successfully updated campaign {campaign.id}",
                extra={"campaign_id": campaign.id, "campaign_name": campaign.name},
            )

            return to_domain(campaign_model)

        except SchedulerError:
            # Already logged and rolled back above
            raise
        except Exception as e:
            session.rollback()
            logger.error(
                f"Unexpected error updating campaign {campaign.id}",
                extra={
                    "campaign_id": campaign.id,
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
            )
            raise DatabaseError(
                f"Failed to update campaign {campaign.id}",
                context={"campaign_id": campaign.id},
                original_error=e,
            ) from e


async def delete_campaign(campaign_id: int) -> None:
    """Delete a campaign and its associated AWS EventBridge schedule group.

    The schedule group deletion cascades to all schedules (main and cycles).

    Args:
        campaign_id: ID of the campaign to delete

    Raises:
        CampaignNotFoundError: If campaign doesn't exist
        SchedulerError: If AWS schedule deletion fails
        DatabaseError: If database operation fails
    """
    logger.info(
        f"Deleting campaign {campaign_id}",
        extra={"campaign_id": campaign_id},
    )

    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = session.get(CampaignSchema, campaign_id)
        if not campaign_model:
            logger.warning(
                f"Campaign {campaign_id} not found for deletion",
                extra={"campaign_id": campaign_id},
            )
            raise CampaignNotFoundError(
                f"Campaign {campaign_id} not found",
                context={"campaign_id": campaign_id},
            )

        campaign_domain = to_domain(campaign_model)

        try:
            # Delete AWS schedule group (cascades to all schedules)
            try:
                await delete_schedule_group(campaign=campaign_domain)
            except ScheduleGroupNotFoundError:
                # Schedule group already deleted - OK to continue
                logger.info(
                    f"Schedule group not found for campaign {campaign_id} (already deleted)",
                    extra={"campaign_id": campaign_id},
                )

            # Delete from database
            session.delete(campaign_model)
            session.commit()

            logger.info(
                f"Successfully deleted campaign {campaign_id}",
                extra={"campaign_id": campaign_id, "campaign_name": campaign_domain.name},
            )

        except SchedulerError as e:
            session.rollback()
            logger.error(
                f"AWS scheduler error deleting campaign {campaign_id}",
                extra={
                    "campaign_id": campaign_id,
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
            )
            raise
        except Exception as e:
            session.rollback()
            logger.error(
                f"Unexpected error deleting campaign {campaign_id}",
                extra={
                    "campaign_id": campaign_id,
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
            )
            raise DatabaseError(
                f"Failed to delete campaign {campaign_id}",
                context={"campaign_id": campaign_id},
                original_error=e,
            ) from e


async def get_campaign(campaign_id: int) -> Campaign | None:
    """Retrieve a campaign by ID and list its schedules.

    Args:
        campaign_id: ID of the campaign to retrieve

    Returns:
        Campaign domain model or None if not found
    """
    logger.debug(
        f"Retrieving campaign {campaign_id}",
        extra={"campaign_id": campaign_id},
    )

    with sessionmaker(bind=echo_engine)() as session:
        campaign_model = session.get(CampaignSchema, campaign_id)
        campaign_domain = to_domain(campaign_model) if campaign_model else None

        if campaign_domain:
            logger.debug(
                f"Retrieved campaign {campaign_id}: {campaign_domain.name}",
                extra={"campaign_id": campaign_id, "campaign_name": campaign_domain.name},
            )

            # List schedules for the campaign
            try:
                schedules = await list_schedules(campaign=campaign_domain)
                logger.debug(
                    f"Found {len(schedules)} schedules for campaign {campaign_id}",
                    extra={
                        "campaign_id": campaign_id,
                        "schedule_count": len(schedules),
                    },
                )
                for schedule in schedules:
                    logger.debug(
                        f"Schedule: {schedule.name} - {schedule.schedule_expression}",
                        extra={
                            "campaign_id": campaign_id,
                            "schedule_name": schedule.name,
                            "schedule_expression": schedule.schedule_expression,
                        },
                    )
            except SchedulerError as e:
                # Log warning but don't fail the get operation
                logger.warning(
                    f"Failed to list schedules for campaign {campaign_id}",
                    extra={
                        "campaign_id": campaign_id,
                        "error_type": type(e).__name__,
                        "error": str(e),
                    },
                )
        else:
            logger.debug(
                f"Campaign {campaign_id} not found",
                extra={"campaign_id": campaign_id},
            )

        return campaign_domain


def list_campaigns() -> List[Campaign]:
    """Retrieve all campaigns.

    Returns:
        List of all campaign domain models

    Raises:
        DatabaseError: If database query fails
    """
    logger.debug("Listing all campaigns")

    try:
        with sessionmaker(bind=echo_engine)() as session:
            campaign_models = session.query(CampaignSchema).all()

        campaigns = [to_domain(campaign_model) for campaign_model in campaign_models]

        logger.debug(
            f"Found {len(campaigns)} campaigns",
            extra={"campaign_count": len(campaigns)},
        )

        return campaigns

    except Exception as e:
        logger.error(
            "Failed to list campaigns",
            extra={
                "error_type": type(e).__name__,
                "error": str(e),
            },
        )
        raise DatabaseError(
            "Failed to list campaigns",
            original_error=e,
        ) from e


# Domain/Schema conversion utilities
def to_domain(model: CampaignSchema) -> Campaign:
    """Convert database schema model to domain model.

    Args:
        model: SQLAlchemy campaign schema

    Returns:
        Campaign domain model
    """
    return Campaign(
        id=model.id,
        name=model.name,
        description=model.description,
        campaign_schedule=model.campaign_schedule,
        cycle_schedule=model.cycle_schedule,
        max_events=model.max_events,
        conn_string=model.conn_string,
    )


def to_schema(campaign: Campaign) -> CampaignSchema:
    """Convert domain model to database schema model.

    Args:
        campaign: Campaign domain model

    Returns:
        SQLAlchemy campaign schema
    """
    return CampaignSchema(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        campaign_schedule=campaign.campaign_schedule,
        cycle_schedule=campaign.cycle_schedule,
        max_events=campaign.max_events,
        conn_string=campaign.conn_string,
    )
