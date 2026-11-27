"""
Silver Layer Incremental Data Loader
=====================================

Responsibilities:
    - Read cleaned Parquet files.
    - Load only new records into PostgreSQL Silver schema.
    - Track the last loaded ID for each table.
    - Use transactional loading.
    - Reuse the existing SQLAlchemy engine.
    - Exclude temporary files.
"""

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import inspect, text

# =====================================================
# Project Paths
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_PATH = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_PATH))


# =====================================================
# Database Connection
# =====================================================

from depi_project.dbconnection.connection import get_engine

# =====================================================
# Configuration
# =====================================================

PARQUET_DIR = PROJECT_ROOT / "cleaned_data"

SCHEMA = "silver"

WATERMARK_TABLE = "etl_watermarks"

PRIMARY_KEY = "id"

EXCLUDED_FILES = {"temp.parquet"}

NO_WATERMARK_FILES = {"customer_activity.parquet"}

CHUNK_SIZE = 10_000


# =====================================================
# Watermark Setup
# =====================================================


def create_watermark_table(engine):

    with engine.begin() as conn:
        conn.execute(
            text(f"""
                CREATE TABLE IF NOT EXISTS {SCHEMA}.{WATERMARK_TABLE} (
                    table_name VARCHAR(255) PRIMARY KEY,
                    last_id BIGINT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )


# =====================================================
# Get Last Loaded ID
# =====================================================


def get_last_loaded_id(conn, table_name):

    result = conn.execute(
        text(f"""
            SELECT last_id
            FROM {SCHEMA}.{WATERMARK_TABLE}
            WHERE table_name = :table_name
        """),
        {"table_name": table_name},
    ).scalar_one_or_none()

    if result is not None:
        return result

    # First run: check existing Silver table
    table_exists = inspect(conn).has_table(table_name, schema=SCHEMA)

    if table_exists:
        result = conn.execute(
            text(f"""
                SELECT MAX({PRIMARY_KEY})
                FROM {SCHEMA}.{table_name}
            """)
        ).scalar()

        return result

    return None


# =====================================================
# Update Watermark
# =====================================================


def update_watermark(conn, table_name, last_id):

    conn.execute(
        text(f"""
            INSERT INTO {SCHEMA}.{WATERMARK_TABLE}
                (table_name, last_id, updated_at)

            VALUES
                (:table_name, :last_id, CURRENT_TIMESTAMP)

            ON CONFLICT (table_name)

            DO UPDATE SET
                last_id = EXCLUDED.last_id,
                updated_at = CURRENT_TIMESTAMP
        """),
        {"table_name": table_name, "last_id": last_id},
    )


# =====================================================
# Incremental Load
# =====================================================


def load_incremental_file(engine, file):

    table_name = file.stem

    print(f"\nProcessing: {SCHEMA}.{table_name}")

    # Read Parquet
    df = pd.read_parquet(file)

    if PRIMARY_KEY not in df.columns:
        raise ValueError(f"Missing primary key '{PRIMARY_KEY}' in {file.name}")

    # Validate ID
    df[PRIMARY_KEY] = pd.to_numeric(df[PRIMARY_KEY], errors="raise")

    if df[PRIMARY_KEY].isna().any():
        raise ValueError(f"Null IDs found in {file.name}")

    # Remove duplicate IDs inside the incoming batch
    df = df.drop_duplicates(subset=[PRIMARY_KEY], keep="last")

    print(f"Total rows in Parquet: {len(df):,}")

    if df.empty:
        print("No data found.")
        return

    # Transaction: data + watermark
    with engine.begin() as conn:
        last_id = get_last_loaded_id(conn, table_name)

        print(f"Last loaded ID: {last_id}")

        # Select only new records
        if last_id is None:
            new_df = df

        else:
            new_df = df[df[PRIMARY_KEY] > last_id]

        if new_df.empty:
            print("No new records. Skipping load.")
            return

        new_df = new_df.sort_values(PRIMARY_KEY)

        new_last_id = new_df[PRIMARY_KEY].max()

        print(f"New rows: {len(new_df):,}")
        print(f"New watermark: {new_last_id}")

        # Load new records
        new_df.to_sql(
            name=table_name,
            con=conn,
            schema=SCHEMA,
            if_exists="append",
            index=False,
            chunksize=CHUNK_SIZE,
            method="multi",
        )

        # Update watermark in same transaction
        update_watermark(conn, table_name, int(new_last_id))

    print(f"Successfully loaded {SCHEMA}.{table_name} | New rows: {len(new_df):,}")


# =====================================================
# Main Loader
# =====================================================


def load_parquet_to_silver():

    engine = get_engine()

    if not PARQUET_DIR.exists():
        raise FileNotFoundError(f"Parquet directory not found: {PARQUET_DIR}")

    parquet_files = sorted(
        PARQUET_DIR.glob("*.parquet"),
        key=lambda file: (file.name == "customer_reviews.parquet", file.name),
    )

    if not parquet_files:
        print("No Parquet files found.")
        return

    print("=" * 60)
    print("Starting Silver Incremental Loading")
    print("=" * 60)

    # Create tracking table
    create_watermark_table(engine)

    for file in parquet_files:
        if file.name in EXCLUDED_FILES or file.name in NO_WATERMARK_FILES:
            print(f"Skipping: {file.name}")
            continue

        try:
            load_incremental_file(engine, file)

        except Exception as e:
            print(f"Failed to load {file.name}")
            print(f"Error: {e}")

            raise

    print("\n" + "=" * 60)
    print("Silver Incremental Loading Completed!")
    print("=" * 60)


# =====================================================
# Main
# =====================================================

if __name__ == "__main__":
    load_parquet_to_silver()
