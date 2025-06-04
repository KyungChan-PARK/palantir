from datetime import timedelta
from typing import Any, Dict, List, Optional

import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import DatabaseManager, with_cache, with_retry
from ..core.security import SecurityManager
from ..models.user import User


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.security = SecurityManager()

    @with_cache(ttl=300)
    @with_retry(max_retries=3)
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """사용자 ID로 사용자를 조회합니다."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    @with_cache(ttl=300)
    @with_retry(max_retries=3)
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """이메일로 사용자를 조회합니다."""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    @with_cache(ttl=300)
    @with_retry(max_retries=3)
    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """사용자 목록을 조회합니다."""
        query = select(User).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    @with_retry(max_retries=3)
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """새로운 사용자를 생성합니다."""
        # 이메일 중복 확인
        existing_user = await self.get_user_by_email(user_data["email"])
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다.",
            )

        # 비밀번호 해싱
        hashed_password = self.security.hash_password(user_data["password"])

        # 사용자 생성
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            hashed_password=hashed_password,
            is_active=True,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        # 캐시 무효화
        redis_client = await DatabaseManager.get_redis()
        await redis_client.delete("get_users:0:100")

        return user

    @with_retry(max_retries=3)
    async def update_user(
        self, user_id: int, user_data: Dict[str, Any]
    ) -> Optional[User]:
        """사용자 정보를 업데이트합니다."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다.",
            )

        # 업데이트할 필드만 처리
        for field, value in user_data.items():
            if field == "password":
                value = self.security.hash_password(value)
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)

        # 캐시 무효화
        redis_client = await DatabaseManager.get_redis()
        await redis_client.delete(f"get_user_by_id:{user_id}")
        await redis_client.delete(f"get_user_by_email:{user.email}")
        await redis_client.delete("get_users:0:100")

        return user

    @with_retry(max_retries=3)
    async def delete_user(self, user_id: int) -> bool:
        """사용자를 삭제합니다."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다.",
            )

        await self.db.delete(user)
        await self.db.commit()

        # 캐시 무효화
        redis_client = await DatabaseManager.get_redis()
        await redis_client.delete(f"get_user_by_id:{user_id}")
        await redis_client.delete(f"get_user_by_email:{user.email}")
        await redis_client.delete("get_users:0:100")

        return True

    @with_retry(max_retries=3)
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """사용자 인증을 수행합니다."""
        user = await self.get_user_by_email(email)
        if not user:
            return None

        if not self.security.verify_password(password, user.hashed_password):
            return None

        return user

    @with_retry(max_retries=3)
    async def create_access_token(self, user: User) -> str:
        """액세스 토큰을 생성합니다."""
        expires_delta = timedelta(minutes=30)
        return self.security.create_token(
            data={"sub": user.email}, expires_delta=expires_delta
        )

    @with_retry(max_retries=3)
    async def verify_token(self, token: str) -> Optional[User]:
        """토큰을 검증하고 사용자를 반환합니다."""
        try:
            payload = self.security.decode_token(token)
            email = payload.get("sub")
            if email is None:
                return None

            return await self.get_user_by_email(email)
        except jwt.PyJWTError:
            return None
