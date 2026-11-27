"""Shared fixtures for the test suite."""

import pandas as pd
import pytest


@pytest.fixture
def sample_df():
    """A small mixed-type DataFrame used across multiple test modules."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "age": [25, 30, 35, 40, 45],
            "salary": [50000.0, 60000.0, 70000.0, 80000.0, 90000.0],
            "department": ["Engineering", "Marketing", "Engineering", "Sales", "Marketing"],
        }
    )


@pytest.fixture
def empty_df():
    """An empty DataFrame with columns."""
    return pd.DataFrame(columns=["id", "name", "age", "salary", "department"])


@pytest.fixture
def df_with_missing():
    """DataFrame with missing values in various columns."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4],
            "name": ["Alice", None, "Charlie", "Diana"],
            "age": [25, 30, None, 40],
            "salary": [50000.0, None, 70000.0, None],
        }
    )


@pytest.fixture
def df_with_duplicates():
    """DataFrame with duplicate rows."""
    return pd.DataFrame(
        {
            "id": [1, 2, 2, 3, 3],
            "name": ["Alice", "Bob", "Bob", "Charlie", "Charlie"],
            "age": [25, 30, 30, 35, 35],
        }
    )


@pytest.fixture
def df_with_negatives():
    """DataFrame with negative values in numeric columns."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "price": [10.0, -5.0, 20.0],
            "quantity": [100, 200, -50],
            "category": ["A", "B", "C"],
        }
    )
