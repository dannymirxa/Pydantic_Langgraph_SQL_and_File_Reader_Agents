import json
from typing import Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import text

def list_tables(db_engine: Engine) -> str:
    """Use this function to get a list of table names in the database.

    Args :
        db_engine (Engine): The SQLAlchemy engine to use.

    Returns :
        str:
    """
    try:
        table_names = inspect(db_engine).get_table_names()
        return json.dumps(table_names)
    except Exception as e:
        return f'Error getting tables: {e}'

def describe_table(db_engine: Engine, table_name: str) -> str:
    """Use this function to get a description of a table in the database.

    Args:
        db_engine (Engine): The SQLAlchemy engine to use.
        table_name (str): The name of the table to describe.

    Returns :
        str: A description of the table.
    """

    try:
        db_inspector = inspect(db_engine)
        table_schema = db_inspector.get_columns(table_name)
        return json.dumps([str(column) for column in table_schema])
    except Exception as e:
        return f'Error getting table schema for table "{table_name}": {e}'

def run_sql_query(db_engine: Engine, query: str, limit: Optional[int] = 10) -> str:
    """Use this function to run a SQL query on the database.

    Args :
        db_engine (Engine): The SQLAlchemy engine to use.
        query (str): The SQL query to run.
        limit (Optional[int]): The maximum number of rows to return.

    Returns :
        str: The result of the query.
    """

    with Session(db_engine) as session, session.begin():
        result = session.execute(text(query))
        try:
            if limit:
                rows = result.fetchmany(limit)
            else:
                rows = result.fetchall()

            recordset = [row._asdict() for row in rows]
            return json.dumps(recordset, default=str)
        except Exception as e:
            return []
        

# db_engine = create_engine('postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment')

# print(run_sql_query(db_engine=db_engine, query="SELECT * FROM artist;"))