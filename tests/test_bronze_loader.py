"""Tests for depi_project.etl.bronze.loader module."""

from unittest.mock import MagicMock, patch, call

import pandas as pd
import pytest

from depi_project.etl.bronze.loader import load_table


class TestLoadTable:
    """Tests for the load_table function."""

    @patch("depi_project.etl.bronze.loader.get_engine")
    def test_returns_dataframe(self, mock_get_engine):
        expected_df = pd.DataFrame({"id": [1, 2], "name": ["A", "B"]})

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_engine.return_value = mock_engine

        with patch("depi_project.etl.bronze.loader.pd.read_sql", return_value=expected_df) as mock_read_sql:
            result = load_table("bronze", "users")

        pd.testing.assert_frame_equal(result, expected_df)
        mock_read_sql.assert_called_once()

    @patch("depi_project.etl.bronze.loader.get_engine")
    def test_query_uses_schema_and_table(self, mock_get_engine):
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_engine.return_value = mock_engine

        with patch("depi_project.etl.bronze.loader.pd.read_sql", return_value=pd.DataFrame()) as mock_read_sql:
            load_table("my_schema", "my_table")

        # Verify the SQL text contains the quoted schema and table
        query_arg = mock_read_sql.call_args[0][0]
        query_text = str(query_arg.text) if hasattr(query_arg, "text") else str(query_arg)
        assert '"my_schema"' in query_text
        assert '"my_table"' in query_text

    @patch("depi_project.etl.bronze.loader.get_engine")
    def test_returns_empty_dataframe_for_empty_table(self, mock_get_engine):
        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_engine.return_value = mock_engine

        empty_df = pd.DataFrame(columns=["id", "name"])

        with patch("depi_project.etl.bronze.loader.pd.read_sql", return_value=empty_df):
            result = load_table("bronze", "empty_table")

        assert result.empty
        assert list(result.columns) == ["id", "name"]
