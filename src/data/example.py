"module"

from sqlalchemy.orm import declarative_base, mapped_column, Mapped
from sqlalchemy import create_engine

# Create a declarative base class
Base = declarative_base()


class CampaignModel(Base):
    "class"

    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column(nullable=True)


def main() -> None:
    "method"
    # Create an SQLite engine (creates the file if it doesn't exist)
    engine = create_engine(
        "sqlite:///example.db", echo=True
    )  # echo=True for SQL logging (optional)

    # Create all tables in the database if they don't exist
    Base.metadata.create_all(engine)

    print("Table 'campaigns' created successfully if it didn't exist.")


if __name__ == "__main__":
    main()
