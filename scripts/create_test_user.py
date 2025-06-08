"""Create a test user in PostgreSQL database."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from palantir.core.config import Settings

def main():
    """Create test user in PostgreSQL database."""
    settings = Settings()
    
    # Create PostgreSQL connection URL
    pg_url = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
        f"{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    
    # Create engine and connect
    engine = create_engine(pg_url)
    
    with engine.connect() as conn:
        # Insert test user using direct values
        conn.execute(text("""
            INSERT INTO users (username, email, full_name, hashed_password, disabled, scopes)
            VALUES ('admin', 'admin@example.com', 'Admin User', 'hashed_password_here', false, '{"admin": true}'::json)
        """))
        conn.commit()
        
        # Verify insertion
        result = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        print(f"Successfully created test user. Total users: {result}")

if __name__ == "__main__":
    main() 