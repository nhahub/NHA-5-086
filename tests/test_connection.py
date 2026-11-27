"""Tests for depi_project.dbconnection.connection module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from depi_project.dbconnection.connection import get_engine


class TestGetEngine:
    """Tests for the get_engine factory function."""

    def setup_method(self):
        """Clear lru_cache before each test so env changes take effect."""
        get_engine.cache_clear()

    def teardown_method(self):
        get_engine.cache_clear()

    @patch.dict(
        os.environ,
        {
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "DB_HOST": "testhost",
            "DB_PORT": "5433",
            "DB_NAME": "testdb",
        },
    )
    @patch("depi_project.dbconnection.connection.create_engine")
    def test_creates_engine_with_env_vars(self, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        engine = get_engine()

        assert engine is mock_engine
        mock_create_engine.assert_called_once()

        # Inspect the URL passed to create_engine
        call_args = mock_create_engine.call_args
        url = call_args[0][0]
        assert str(url).startswith("postgresql+psycopg2://")
        assert "testuser" in str(url)
        assert "testhost" in str(url)
        assert "5433" in str(url)
        assert "testdb" in str(url)

    @patch.dict(
        os.environ,
        {
            "DB_USER": "user",
            "DB_PASSWORD": "pass",
            "DB_NAME": "mydb",
        },
        clear=False,
    )
    @patch("depi_project.dbconnection.connection.create_engine")
    def test_uses_default_host_and_port(self, mock_create_engine):
        # Remove HOST and PORT so defaults kick in
        os.environ.pop("DB_HOST", None)
        os.environ.pop("DB_PORT", None)

        mock_create_engine.return_value = MagicMock()
        get_engine()

        url = mock_create_engine.call_args[0][0]
        assert "localhost" in str(url)
        assert "5432" in str(url)

    @patch.dict(
        os.environ,
        {
            "DB_USER": "user",
            "DB_PASSWORD": "pass",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "mydb",
        },
    )
    @patch("depi_project.dbconnection.connection.create_engine")
    def test_engine_is_cached(self, mock_create_engine):
        mock_create_engine.return_value = MagicMock()

        engine1 = get_engine()
        engine2 = get_engine()

        assert engine1 is engine2
        # create_engine should only be called once due to lru_cache
        mock_create_engine.assert_called_once()

    @patch.dict(
        os.environ,
        {
            "DB_USER": "user",
            "DB_PASSWORD": "pass",
            "DB_HOST": "localhost",
            "DB_PORT": "5432",
            "DB_NAME": "mydb",
        },
    )
    @patch("depi_project.dbconnection.connection.create_engine")
    def test_pool_pre_ping_enabled(self, mock_create_engine):
        mock_create_engine.return_value = MagicMock()
        get_engine()

        call_kwargs = mock_create_engine.call_args[1]
        assert call_kwargs.get("pool_pre_ping") is True
