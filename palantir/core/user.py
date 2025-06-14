# mypy: ignore-errors
from sqlalchemy import JSON, Boolean, Column, Integer, String
from sqlalchemy.orm import declarative_base, Session
from typing import Optional, List, Dict, Any

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

    @classmethod
    def get_by_username(cls, username: str) -> Optional["UserDB"]:
        from .database import get_db
        db = next(get_db())
        return db.query(cls).filter(cls.username == username).first()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "disabled": self.disabled,
            "scopes": self.scopes
        }
