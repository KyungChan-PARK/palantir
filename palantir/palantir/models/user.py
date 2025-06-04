from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """사용자 모델입니다."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 복합 인덱스 추가
    __table_args__ = (
        # 이메일과 사용자명으로 빠른 검색
        Index("idx_email_username", "email", "username"),
        # 활성 사용자 검색 최적화
        Index("idx_active_created", "is_active", "created_at"),
        # 사용자명 검색 최적화
        Index("idx_username_lower", func.lower("username")),
        # 이메일 검색 최적화
        Index("idx_email_lower", func.lower("email")),
    )

    def __repr__(self):
        return f"<User {self.email}>"

    def to_dict(self):
        """사용자 정보를 딕셔너리로 변환합니다."""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """딕셔너리로부터 사용자 객체를 생성합니다."""
        return cls(
            email=data.get("email"),
            username=data.get("username"),
            hashed_password=data.get("hashed_password"),
            is_active=data.get("is_active", True),
        )
