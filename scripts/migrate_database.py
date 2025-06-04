#!/usr/bin/env python

import asyncio
import logging
from typing import List
import asyncpg

from palantir.core.database import DatabaseManager
from palantir.models.user import User

logger = logging.getLogger(__name__)

async def create_tables(pool: asyncpg.Pool):
    """테이블을 생성합니다."""
    async with pool.acquire() as conn:
        # 사용자 테이블 생성
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                username VARCHAR(50) NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """)
        
        # 인덱스 생성
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
            CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);
            CREATE INDEX IF NOT EXISTS idx_email_username ON users(email, username);
            CREATE INDEX IF NOT EXISTS idx_active_created ON users(is_active, created_at);
            CREATE INDEX IF NOT EXISTS idx_username_lower ON users(LOWER(username));
            CREATE INDEX IF NOT EXISTS idx_email_lower ON users(LOWER(email));
        """)
        
        # 고유 제약 조건 추가
        await conn.execute("""
            ALTER TABLE users ADD CONSTRAINT users_email_unique UNIQUE (email);
            ALTER TABLE users ADD CONSTRAINT users_username_unique UNIQUE (username);
        """)
        
        logger.info("테이블과 인덱스가 생성되었습니다.")

async def optimize_tables(pool: asyncpg.Pool):
    """테이블을 최적화합니다."""
    async with pool.acquire() as conn:
        # 테이블 분석
        await conn.execute("ANALYZE users")
        
        # 인덱스 재구성
        await conn.execute("REINDEX TABLE users")
        
        # 통계 업데이트
        await conn.execute("""
            UPDATE pg_statistic 
            SET stakind1 = 1, 
                staop1 = 0, 
                stanumbers1 = ARRAY[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
            WHERE starelid = 'users'::regclass
        """)
        
        logger.info("테이블이 최적화되었습니다.")

async def migrate():
    """데이터베이스 마이그레이션을 실행합니다."""
    try:
        # 데이터베이스 연결 풀 초기화
        await DatabaseManager.initialize(
            dsn="postgresql://postgres:postgres@localhost:5432/palantir",
            redis_url="redis://localhost:6379/0"
        )
        
        pool = await DatabaseManager.get_pool()
        
        # 테이블 생성
        await create_tables(pool)
        
        # 테이블 최적화
        await optimize_tables(pool)
        
        logger.info("마이그레이션이 완료되었습니다.")
        
    except Exception as e:
        logger.error(f"마이그레이션 중 오류가 발생했습니다: {str(e)}")
        raise
    finally:
        await DatabaseManager.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(migrate()) 