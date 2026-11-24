"""Data cleaning and validation module."""

import pandas as pd
from depi_project.etl.bronze.loader import load_table

# =========================
# DataFrame Validation
# =========================


def check_dataframe(data):
    """Check whether the input is a Pandas DataFrame."""

    return isinstance(data, pd.DataFrame)


# =========================
# Data Type Selection
# =========================


def numerical_data(data):
    if not check_dataframe(data):
        raise TypeError("Please enter a DataFrame")

    return data.select_dtypes(include=["number"])


def categorical_data(data):
    if not check_dataframe(data):
        raise TypeError("Please enter a DataFrame")

    return data.select_dtypes(include=["object", "category", "bool", "string"])


# =========================
# Data Inspection
# =========================


def get_information(data):
    if not check_dataframe(data):
        raise TypeError("Please enter a DataFrame")

    print(f"Number of rows: {data.shape[0]}")
    print(f"Number of columns: {data.shape[1]}")

    print("-" * 60)
    data.info()

    print("-" * 60)
    print(data.describe(include="all"))


def check_missing_values(data):
    if not check_dataframe(data):
        raise TypeError("Please enter a DataFrame")

    print("Missing Values Per Column:")
    print(data.isnull().sum())

    print("-" * 60)

    total_missing = data.isnull().sum().sum()
    print(f"Total Missing Values: {total_missing}")

    print("-" * 60)

    if data.empty:
        print("Cannot calculate missing percentage: DataFrame is empty")
        return

    missing_percentage = (data.isnull().sum() / len(data)) * 100

    print("Missing Values Percentage:")
    print(missing_percentage)


def check_duplicates(data):
    if not check_dataframe(data):
        raise TypeError("Please enter a DataFrame")

    duplicates = data.duplicated()

    print(f"Number of Duplicated Rows: {duplicates.sum()}")

    print("-" * 60)
    print("Duplicated Rows:")
    print(data[duplicates])


def check_data_type(data):
    if not check_dataframe(data):
        raise TypeError("Please enter a DataFrame")

    print("Data Types Per Column:")
    print(data.dtypes)


# =========================
# Data Validity Checks
# =========================


def numeric_validity_checks(data, positive_columns=None):
    if not check_dataframe(data):
        raise TypeError("Please enter a DataFrame")

    numeric_df = numerical_data(data)

    # Only check positivity for columns that require it
    positive_columns = positive_columns or []

    for col in positive_columns:
        if col not in numeric_df.columns:
            print(f"Column {col} is not a numeric column")
            continue

        if (numeric_df[col] <= 0).any():
            print(f"Column {col} needs cleaning")
        else:
            print(f"Column {col} is suitable")


def categorical_validity_checks(data):
    if not check_dataframe(data):
        raise TypeError("Please enter a DataFrame")

    cat_df = categorical_data(data)

    for col in cat_df.columns:
        empty_values = cat_df[col].notna() & cat_df[col].astype(
            "string"
        ).str.strip().eq("")

        if empty_values.any():
            print(f"Column {col} needs cleaning")
        else:
            print(f"Column {col} is suitable")


def validate_dataframe(data):
    if not check_dataframe(data):
        raise TypeError("Please enter a DataFrame")

    get_information(data)
    check_missing_values(data)
    check_duplicates(data)
    check_data_type(data)
    categorical_validity_checks(data)


# =========================
# Main
# =========================


def main():
    df = load_table(input("Enter schema name: "), input("Enter table name: "))

    validate_dataframe(df)


if __name__ == "__main__":
    main()
