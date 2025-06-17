"""Database utilities for DuckDB connections."""

import contextlib
from pathlib import Path
from typing import Generator, Optional
import os

import duckdb
from prefect.logging import get_run_logger


@contextlib.contextmanager
def get_duckdb_connection(
    db_path: Optional[str] = None,
    read_only: bool = False,
    schema: Optional[str] = None,
) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Context manager for DuckDB connections.

    Args:
        db_path: Path to the database file. If None, uses in-memory database.
        read_only: Whether to open the connection in read-only mode.

    Yields:
        DuckDB connection object.
    """
    logger = get_run_logger()
    db_path = db_path or os.getenv("DUCKDB_PATH")
    schema = schema or os.getenv("DUCKDB_SCHEMA")

    if db_path:
        path = Path(db_path)
        logger.info(f"Connecting to DuckDB at {path}")
    else:
        logger.info("Using in-memory DuckDB database")

    try:
        conn = duckdb.connect(db_path, read_only=read_only)
        if schema:
            conn.execute(f"SET schema '{schema}'")
        yield conn
    finally:
        conn.close()
        logger.info("DuckDB connection closed")


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the database with required tables and schemas.

    Args:
        db_path: Path to the database file.
    """
    logger = get_run_logger()
    db_path = db_path or os.getenv("DUCKDB_PATH")
    logger.info(f"Initializing database at {db_path}")

    with get_duckdb_connection(db_path) as conn:
        # Create metadata table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                table_name VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                row_count BIGINT,
                schema JSON
            )
        """
        )

        # Create data lineage table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS data_lineage (
                flow_id VARCHAR,
                source_table VARCHAR,
                target_table VARCHAR,
                transformation_type VARCHAR,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                parameters JSON
            )
        """
        )

    logger.info("Database initialized successfully")
