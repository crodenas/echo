"module"

from sqlalchemy.orm import declarative_base, mapped_column, Mapped
from sqlalchemy import URL, Engine, create_engine
from sqlalchemy.orm import sessionmaker

# Create a declarative base class
Base = declarative_base()


class CampaignModel(Base):
    "class"

    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column(nullable=True)


def make_engine(db_url: str | URL, echo: bool = True) -> Engine:
    "function"
    # Create an SQLite engine (creates the file if it doesn't exist)
    return create_engine(db_url, echo=echo)  # echo=True for SQL logging (optional)


engine = make_engine("sqlite:///example.db", echo=True)

# Create all tables in the database if they don't exist
Base.metadata.create_all(engine)

print("Table 'campaigns' created successfully if it didn't exist.")

# Create a session factory bound to the engine
Session = sessionmaker(bind=engine)

with Session() as session:
    # Example usage: Add a new campaign
    new_campaign = CampaignModel(
        name="New Campaign", description="This is a new campaign."
    )
    session.add(new_campaign)
    session.commit()
    print(f"Added campaign with ID: {new_campaign.id}")

__all__ = ["engine", "Session", "CampaignModel", "Base"]
