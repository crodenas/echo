"module"

from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, sessionmaker

# Create a declarative base class
Base = declarative_base()


class CampaignModel(Base):
    "class"

    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column(nullable=True)
