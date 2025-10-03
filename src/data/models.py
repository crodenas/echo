"module"

from sqlalchemy.orm import declarative_base, mapped_column, Mapped
from db_engine import engine


Base = declarative_base()


class CampaignModel(Base):
    "class"

    __tablename__ = "campaigns"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column(nullable=True)


def create_tables() -> None:
    "method"
    Base.metadata.create_all(engine)


# # infrastructure/mappers.py
# def to_domain(model: UserModel) -> User:
#     return User(id=model.id, email=model.email, name=model.name)


# def to_model(user: User) -> UserModel:
#     return UserModel(id=user.id, email=user.email, name=user.name)
