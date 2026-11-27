"""Tests for depi_project.etl.silver.load_script module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pandas as pd
import pytest

from depi_project.etl.silver.load_script import (
    EXCLUDED_FILES,
    NO_WATERMARK_FILES,
    PRIMARY_KEY,
    SCHEMA,
    load_incremental_file,
    load_parquet_to_silver,
)


# =============================================================================
# Configuration constants
# =============================================================================


class TestConfiguration:
    def test_schema_is_silver(self):
        assert SCHEMA == "silver"

    def test_primary_key_is_id(self):
        assert PRIMARY_KEY == "id"

    def test_temp_is_excluded(self):
        assert "temp.parquet" in EXCLUDED_FILES

    def test_customer_activity_no_watermark(self):
        assert "customer_activity.parquet" in NO_WATERMARK_FILES


# =============================================================================
# load_incremental_file
# =============================================================================


class TestLoadIncrementalFile:
    def _make_parquet(self, tmp_path, name, df):
        """Helper: write a DataFrame as a Parquet file and return the Path."""
        file = tmp_path / name
        df.to_parquet(file, index=False)
        return file

    def test_raises_on_missing_primary_key(self, tmp_path):
        df = pd.DataFrame({"name": ["A", "B"], "value": [1, 2]})
        file = self._make_parquet(tmp_path, "test_table.parquet", df)

        mock_engine = MagicMock()

        with pytest.raises(ValueError, match="Missing primary key"):
            load_incremental_file(mock_engine, file)

    def test_raises_on_null_ids(self, tmp_path):
        df = pd.DataFrame({"id": [1, None, 3], "value": [10, 20, 30]})
        file = self._make_parquet(tmp_path, "test_table.parquet", df)

        mock_engine = MagicMock()

        with pytest.raises(ValueError, match="Null IDs found"):
            load_incremental_file(mock_engine, file)

    def test_skips_load_when_no_new_records(self, tmp_path, capsys):
        df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        file = self._make_parquet(tmp_path, "test_table.parquet", df)

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        # Pretend last loaded id is 10 (greater than any id in the file)
        with patch(
            "depi_project.etl.silver.load_script.get_last_loaded_id",
            return_value=10,
        ):
            load_incremental_file(mock_engine, file)

        captured = capsys.readouterr()
        assert "No new records" in captured.out

    def test_loads_all_records_on_first_run(self, tmp_path, capsys):
        df = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        file = self._make_parquet(tmp_path, "test_table.parquet", df)

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "depi_project.etl.silver.load_script.get_last_loaded_id",
            return_value=None,
        ), patch(
            "depi_project.etl.silver.load_script.update_watermark"
        ) as mock_watermark:
            load_incremental_file(mock_engine, file)

        captured = capsys.readouterr()
        assert "New rows: 3" in captured.out
        mock_watermark.assert_called_once_with(mock_conn, "test_table", 3)

    def test_loads_only_new_records(self, tmp_path, capsys):
        df = pd.DataFrame({"id": [1, 2, 3, 4, 5], "value": [10, 20, 30, 40, 50]})
        file = self._make_parquet(tmp_path, "test_table.parquet", df)

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "depi_project.etl.silver.load_script.get_last_loaded_id",
            return_value=3,
        ), patch(
            "depi_project.etl.silver.load_script.update_watermark"
        ) as mock_watermark:
            load_incremental_file(mock_engine, file)

        captured = capsys.readouterr()
        assert "New rows: 2" in captured.out
        mock_watermark.assert_called_once_with(mock_conn, "test_table", 5)

    def test_deduplicates_ids_in_batch(self, tmp_path, capsys):
        df = pd.DataFrame({"id": [1, 2, 2, 3], "value": [10, 20, 25, 30]})
        file = self._make_parquet(tmp_path, "test_table.parquet", df)

        mock_conn = MagicMock()
        mock_engine = MagicMock()
        mock_engine.begin.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.begin.return_value.__exit__ = MagicMock(return_value=False)

        with patch(
            "depi_project.etl.silver.load_script.get_last_loaded_id",
            return_value=None,
        ), patch(
            "depi_project.etl.silver.load_script.update_watermark"
        ):
            load_incremental_file(mock_engine, file)

        captured = capsys.readouterr()
        # After dedup, should have 3 rows (ids: 1, 2, 3)
        assert "Total rows in Parquet: 3" in captured.out

    def test_empty_parquet_skips(self, tmp_path, capsys):
        df = pd.DataFrame({"id": pd.array([], dtype="int64"), "value": pd.array([], dtype="int64")})
        file = self._make_parquet(tmp_path, "test_table.parquet", df)

        mock_engine = MagicMock()

        load_incremental_file(mock_engine, file)

        captured = capsys.readouterr()
        assert "No data found" in captured.out


# =============================================================================
# load_parquet_to_silver
# =============================================================================


class TestLoadParquetToSilver:
    @patch("depi_project.etl.silver.load_script.get_engine")
    @patch("depi_project.etl.silver.load_script.PARQUET_DIR")
    def test_raises_if_parquet_dir_missing(self, mock_dir, mock_get_engine):
        mock_dir.exists.return_value = False
        mock_dir.__str__ = lambda self: "/nonexistent"

        with pytest.raises(FileNotFoundError, match="Parquet directory not found"):
            load_parquet_to_silver()

    @patch("depi_project.etl.silver.load_script.get_engine")
    @patch("depi_project.etl.silver.load_script.PARQUET_DIR")
    @patch("depi_project.etl.silver.load_script.create_watermark_table")
    def test_prints_message_when_no_files(self, mock_create, mock_dir, mock_get_engine, capsys):
        mock_dir.exists.return_value = True
        mock_dir.glob.return_value = []

        load_parquet_to_silver()

        captured = capsys.readouterr()
        assert "No Parquet files found" in captured.out

    @patch("depi_project.etl.silver.load_script.get_engine")
    @patch("depi_project.etl.silver.load_script.PARQUET_DIR")
    @patch("depi_project.etl.silver.load_script.create_watermark_table")
    @patch("depi_project.etl.silver.load_script.load_incremental_file")
    def test_skips_excluded_and_no_watermark_files(
        self, mock_load, mock_create, mock_dir, mock_get_engine, capsys
    ):
        mock_dir.exists.return_value = True

        # Simulate file list with excluded + no-watermark + valid
        temp_file = MagicMock()
        temp_file.name = "temp.parquet"
        activity_file = MagicMock()
        activity_file.name = "customer_activity.parquet"
        valid_file = MagicMock()
        valid_file.name = "users.parquet"

        mock_dir.glob.return_value = [temp_file, activity_file, valid_file]

        load_parquet_to_silver()

        captured = capsys.readouterr()
        assert "Skipping: temp.parquet" in captured.out
        assert "Skipping: customer_activity.parquet" in captured.out

        # Only the valid file should be loaded
        mock_load.assert_called_once()
