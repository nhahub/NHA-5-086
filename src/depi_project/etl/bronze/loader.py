import pandas as pd
from depi_project.dbconnection import get_engine
from sqlalchemy import text


def load_table(schema: str, table: str) -> pd.DataFrame:
    engine = get_engine()

    query = text(f'SELECT * FROM "{schema}"."{table}"')

    with engine.connect() as connection:
        df = pd.read_sql(query, connection)

    return df
