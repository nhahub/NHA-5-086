"""Tests for depi_project.cleaning.check module."""

import pandas as pd
import pytest

from depi_project.cleaning.check import (
    categorical_data,
    categorical_validity_checks,
    check_dataframe,
    check_duplicates,
    check_missing_values,
    check_data_type,
    get_information,
    numerical_data,
    numeric_validity_checks,
    validate_dataframe,
)


# =============================================================================
# check_dataframe
# =============================================================================


class TestCheckDataframe:
    def test_valid_dataframe(self, sample_df):
        assert check_dataframe(sample_df) is True

    def test_empty_dataframe(self, empty_df):
        assert check_dataframe(empty_df) is True

    def test_rejects_dict(self):
        assert check_dataframe({"a": 1}) is False

    def test_rejects_list(self):
        assert check_dataframe([1, 2, 3]) is False

    def test_rejects_string(self):
        assert check_dataframe("hello") is False

    def test_rejects_none(self):
        assert check_dataframe(None) is False

    def test_rejects_series(self):
        assert check_dataframe(pd.Series([1, 2, 3])) is False

    def test_rejects_int(self):
        assert check_dataframe(42) is False


# =============================================================================
# numerical_data
# =============================================================================


class TestNumericalData:
    def test_selects_numeric_columns(self, sample_df):
        result = numerical_data(sample_df)
        assert list(result.columns) == ["id", "age", "salary"]

    def test_empty_dataframe(self, empty_df):
        result = numerical_data(empty_df)
        assert result.empty

    def test_raises_on_non_dataframe(self):
        with pytest.raises(TypeError, match="Please enter a DataFrame"):
            numerical_data("not a dataframe")

    def test_all_numeric(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
        result = numerical_data(df)
        assert list(result.columns) == ["a", "b"]

    def test_no_numeric_columns(self):
        df = pd.DataFrame({"name": ["Alice", "Bob"], "city": ["NY", "LA"]})
        result = numerical_data(df)
        assert result.empty
        assert len(result.columns) == 0


# =============================================================================
# categorical_data
# =============================================================================


class TestCategoricalData:
    def test_selects_categorical_columns(self, sample_df):
        result = categorical_data(sample_df)
        assert list(result.columns) == ["name", "department"]

    def test_raises_on_non_dataframe(self):
        with pytest.raises(TypeError, match="Please enter a DataFrame"):
            categorical_data([1, 2, 3])

    def test_includes_bool_columns(self):
        df = pd.DataFrame({"flag": [True, False], "name": ["A", "B"], "val": [1, 2]})
        result = categorical_data(df)
        assert "flag" in result.columns
        assert "name" in result.columns
        assert "val" not in result.columns

    def test_includes_category_dtype(self):
        df = pd.DataFrame({"cat_col": pd.Categorical(["a", "b", "c"]), "num": [1, 2, 3]})
        result = categorical_data(df)
        assert "cat_col" in result.columns
        assert "num" not in result.columns

    def test_no_categorical_columns(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})
        result = categorical_data(df)
        assert result.empty


# =============================================================================
# get_information
# =============================================================================


class TestGetInformation:
    def test_runs_without_error(self, sample_df, capsys):
        get_information(sample_df)
        captured = capsys.readouterr()
        assert "Number of rows: 5" in captured.out
        assert "Number of columns: 5" in captured.out

    def test_raises_on_non_dataframe(self):
        with pytest.raises(TypeError, match="Please enter a DataFrame"):
            get_information("not a dataframe")


# =============================================================================
# check_missing_values
# =============================================================================


class TestCheckMissingValues:
    def test_no_missing(self, sample_df, capsys):
        check_missing_values(sample_df)
        captured = capsys.readouterr()
        assert "Total Missing Values: 0" in captured.out

    def test_with_missing(self, df_with_missing, capsys):
        check_missing_values(df_with_missing)
        captured = capsys.readouterr()
        assert "Total Missing Values: 4" in captured.out

    def test_empty_dataframe(self, empty_df, capsys):
        check_missing_values(empty_df)
        captured = capsys.readouterr()
        assert "Cannot calculate missing percentage" in captured.out

    def test_raises_on_non_dataframe(self):
        with pytest.raises(TypeError, match="Please enter a DataFrame"):
            check_missing_values(None)


# =============================================================================
# check_duplicates
# =============================================================================


class TestCheckDuplicates:
    def test_no_duplicates(self, sample_df, capsys):
        check_duplicates(sample_df)
        captured = capsys.readouterr()
        assert "Number of Duplicated Rows: 0" in captured.out

    def test_with_duplicates(self, df_with_duplicates, capsys):
        check_duplicates(df_with_duplicates)
        captured = capsys.readouterr()
        assert "Number of Duplicated Rows: 2" in captured.out

    def test_raises_on_non_dataframe(self):
        with pytest.raises(TypeError, match="Please enter a DataFrame"):
            check_duplicates("not a dataframe")


# =============================================================================
# check_data_type
# =============================================================================


class TestCheckDataType:
    def test_prints_dtypes(self, sample_df, capsys):
        check_data_type(sample_df)
        captured = capsys.readouterr()
        assert "Data Types Per Column:" in captured.out

    def test_raises_on_non_dataframe(self):
        with pytest.raises(TypeError, match="Please enter a DataFrame"):
            check_data_type(42)


# =============================================================================
# numeric_validity_checks
# =============================================================================


class TestNumericValidityChecks:
    def test_positive_columns_valid(self, sample_df, capsys):
        numeric_validity_checks(sample_df, positive_columns=["age", "salary"])
        captured = capsys.readouterr()
        assert "age is suitable" in captured.out
        assert "salary is suitable" in captured.out

    def test_positive_columns_invalid(self, df_with_negatives, capsys):
        numeric_validity_checks(df_with_negatives, positive_columns=["price", "quantity"])
        captured = capsys.readouterr()
        assert "price needs cleaning" in captured.out
        assert "quantity needs cleaning" in captured.out

    def test_no_positive_columns(self, sample_df, capsys):
        numeric_validity_checks(sample_df)
        captured = capsys.readouterr()
        # No output expected for positivity since no columns specified
        assert captured.out == ""

    def test_non_numeric_column_skipped(self, df_with_negatives, capsys):
        numeric_validity_checks(df_with_negatives, positive_columns=["category"])
        captured = capsys.readouterr()
        assert "category is not a numeric column" in captured.out

    def test_raises_on_non_dataframe(self):
        with pytest.raises(TypeError, match="Please enter a DataFrame"):
            numeric_validity_checks("not a dataframe")


# =============================================================================
# categorical_validity_checks
# =============================================================================


class TestCategoricalValidityChecks:
    def test_valid_categories(self, sample_df, capsys):
        categorical_validity_checks(sample_df)
        captured = capsys.readouterr()
        assert "name is suitable" in captured.out
        assert "department is suitable" in captured.out

    def test_empty_string_values(self, capsys):
        df = pd.DataFrame({"status": ["active", "  ", "inactive"]})
        categorical_validity_checks(df)
        captured = capsys.readouterr()
        assert "status needs cleaning" in captured.out

    def test_raises_on_non_dataframe(self):
        with pytest.raises(TypeError, match="Please enter a DataFrame"):
            categorical_validity_checks(None)


# =============================================================================
# validate_dataframe
# =============================================================================


class TestValidateDataframe:
    def test_runs_all_checks(self, sample_df, capsys):
        validate_dataframe(sample_df)
        captured = capsys.readouterr()
        # Should contain output from multiple sub-checks
        assert "Number of rows:" in captured.out
        assert "Missing Values Per Column:" in captured.out
        assert "Number of Duplicated Rows:" in captured.out
        assert "Data Types Per Column:" in captured.out

    def test_raises_on_non_dataframe(self):
        with pytest.raises(TypeError, match="Please enter a DataFrame"):
            validate_dataframe([1, 2, 3])
