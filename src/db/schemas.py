"module"

from sqlalchemy.orm import Mapped, declarative_base, mapped_column

from db.db_engine import echo_engine

Base = declarative_base()


class CampaignSchema(Base):
    "class"

    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column(nullable=True)
    cycle_schedule: Mapped[str | None] = mapped_column(nullable=True)
    escalation_schedule: Mapped[str | None] = mapped_column(nullable=True)


def create_tables(engine) -> None:
    "method"
    Base.metadata.create_all(engine)


create_tables(echo_engine)
