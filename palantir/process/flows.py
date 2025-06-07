"""ETL flow definitions using Prefect."""

from pathlib import Path
from typing import Optional

import pandas as pd
from prefect import flow, task
from prefect.logging import get_run_logger


@task
def extract_csv(file_path: Path) -> pd.DataFrame:
    """Extract data from CSV file."""
    logger = get_run_logger()
    logger.info(f"Extracting data from {file_path}")
    return pd.read_csv(file_path)


@task
def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Transform the extracted data."""
    logger = get_run_logger()
    logger.info("Transforming data")
    
    # Add your transformation logic here
    # Example: Basic cleaning
    df = df.dropna()
    df = df.drop_duplicates()
    
    return df


@task
def load_to_duckdb(df: pd.DataFrame, table_name: str, db_path: Optional[str] = None) -> None:
    """Load transformed data to DuckDB."""
    import duckdb
    
    logger = get_run_logger()
    logger.info(f"Loading data to table {table_name}")
    
    # Connect to DuckDB (in-memory if no path provided)
    conn = duckdb.connect(db_path) if db_path else duckdb.connect()
    
    # Create table and load data
    conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM df")
    conn.close()
    
    logger.info("Data loaded successfully")


@flow(name="csv_to_duckdb")
def csv_to_duckdb_flow(
    csv_path: str,
    table_name: str,
    db_path: Optional[str] = None
) -> None:
    """Main ETL flow for processing CSV files to DuckDB."""
    # Convert string path to Path object
    file_path = Path(csv_path)
    
    # Execute the ETL pipeline
    raw_data = extract_csv(file_path)
    transformed_data = transform_data(raw_data)
    load_to_duckdb(transformed_data, table_name, db_path)


if __name__ == "__main__":
    # Example usage
    csv_to_duckdb_flow(
        csv_path="sample.csv",
        table_name="example_table",
        db_path="data.db"
    ) 