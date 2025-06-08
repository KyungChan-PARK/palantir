"""PostgreSQL migration script for Palantir project."""

import os
import sys
from pathlib import Path
from typing import List, Optional

import alembic.config
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from palantir.auth.models import Base as AuthBase
from palantir.core.user import Base as CoreBase
from palantir.core.config import Settings

def create_pg_url(settings: Settings) -> str:
    """Create PostgreSQL connection URL from settings."""
    return (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
        f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )

def setup_alembic(pg_url: str) -> Config:
    """Setup Alembic configuration."""
    config = Config()
    config.set_main_option("script_location", "migrations")
    config.set_main_option("sqlalchemy.url", pg_url)
    return config

def create_pg_engine(pg_url: str) -> Engine:
    """Create SQLAlchemy engine for PostgreSQL."""
    return create_engine(pg_url, pool_pre_ping=True)

def check_pg_connection(engine: Engine) -> bool:
    """Check if PostgreSQL connection is available."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except OperationalError:
        return False

def migrate_table_data(
    sqlite_session: Session,
    pg_session: Session,
    table_name: str,
    batch_size: int = 1000
) -> int:
    """Migrate data from SQLite to PostgreSQL table."""
    total_migrated = 0
    while True:
        # Fetch batch from SQLite
        results = sqlite_session.execute(
            text(f"SELECT * FROM {table_name} LIMIT {batch_size} OFFSET {total_migrated}")
        ).fetchall()
        
        if not results:
            break
            
        # Insert into PostgreSQL
        pg_session.execute(
            text(f"INSERT INTO {table_name} VALUES ({','.join([':%d' % i for i in range(len(results[0]))])})"),
            [dict(zip(result.keys(), result)) for result in results]
        )
        pg_session.commit()
        
        total_migrated += len(results)
        print(f"Migrated {total_migrated} rows from {table_name}")
    
    return total_migrated

def main():
    """Main migration function."""
    settings = Settings()
    pg_url = create_pg_url(settings)
    
    # Setup database engines
    pg_engine = create_pg_engine(pg_url)
    sqlite_engine = create_engine(
        "sqlite:///./users.db",
        connect_args={"check_same_thread": False}
    )
    
    # Check PostgreSQL connection
    if not check_pg_connection(pg_engine):
        print("Error: Could not connect to PostgreSQL. Please check your configuration.")
        sys.exit(1)
    
    # Create PostgreSQL tables
    AuthBase.metadata.create_all(pg_engine)
    CoreBase.metadata.create_all(pg_engine)
    
    # Setup sessions
    sqlite_session = Session(sqlite_engine)
    pg_session = Session(pg_engine)
    
    try:
        # Migrate Users table
        users_count = migrate_table_data(sqlite_session, pg_session, "users")
        print(f"Successfully migrated {users_count} users")
        
        # Setup Alembic for future migrations
        alembic_cfg = setup_alembic(pg_url)
        command.stamp(alembic_cfg, "head")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        pg_session.rollback()
        sys.exit(1)
        
    finally:
        sqlite_session.close()
        pg_session.close()

if __name__ == "__main__":
    main() 