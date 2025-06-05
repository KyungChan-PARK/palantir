# mypy: ignore-errors
from sqlalchemy import JSON, Boolean, Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserDB(Base):  # type: ignore[misc]
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)
    scopes = Column(JSON)
