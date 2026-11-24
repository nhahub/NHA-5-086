"""
Database Connection Module
==========================

This module handles database connectivity using SQLAlchemy.

Responsibilities:
    - Establish a connection to the PostgreSQL database.
    - Manage database engine configuration.
    - Provide reusable database connection functionality.
    - Handle connection errors.

Dependencies:
    - SQLAlchemy
    - psycopg2
    - python-dotenv
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from functools import lru_cache

load_dotenv()


@lru_cache(maxsize=1)
def get_engine():
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME"),
    )
    return create_engine(url, pool_pre_ping=True)


def test_connection():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Connected:", result.scalar())


if __name__ == "__main__":
    test_connection()
