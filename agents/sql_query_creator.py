import sys

# adding Folder_2 to the system path
# sys.path.insert(0, 'utils')
from util_functions.sql_operations import list_tables, describe_table, run_sql_query
from models import ACTIVE_MODEL

from dotenv import load_dotenv
from dataclasses import dataclass
import pandas as pd
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypeAlias, Union, Optional
from annotated_types import MinLen
from pydantic_ai import Agent, ModelRetry, RunContext

from sqlalchemy import Engine, create_engine

load_dotenv("/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/.env")

class SQLSuccess(BaseModel):
    sql_query: Annotated[str, MinLen(1)] = Field(alias='sql_query', description='SQL query to run')
    detail: str = Field(alias='detail', description='Explanation of the SQL query, steps taken, the result of the query (JSON)')
    query_results_json: Optional[str] = Field(None, alias='query_results_json', description='JSON string of the query results')
    
class InvalidRequest(BaseModel):
    error_message: str

SQLResponse: TypeAlias = Union[
                                SQLSuccess,     
                                InvalidRequest
                            ]

@dataclass
class Dependencies:
    db_engine: Engine

sql_query_creator_agent = Agent(
    model=ACTIVE_MODEL,
    output_type=SQLResponse,
    result_retries=3,
    model_settings={'temperature': 0.1, 'max_tokens': 1000}
)

@sql_query_creator_agent.system_prompt
def system_prompt(ctx: RunContext[Dependencies]) -> str:
    return f"""\
    You are an AI agent equipped with database tools. Your goal is to help users interact with a database by generating and executing SQL queries, and if requested, facilitate chart generation.

    Follow these steps:
    1.  **List Tables:** If you are unsure about available tables, use the `list_tables_tool` once.
    2.  **Describe Table:** Use `describe_table_tool` ONLY for the specific table(s) directly relevant to the user's request. Be precise and avoid describing unnecessary tables.
    3.  **Handle Sales/Revenue Queries:** If the user's request involves "sales", "revenue", or "total amount", remember that this data is typically derived from the `invoice_line` table (which has `unit_price` and `quantity`). You will likely need to join `artist`, `album`, `track`, and `invoice_line` tables to fulfill such requests. Calculate sales as `SUM(invoice_line.unit_price * invoice_line.quantity)`.
    4.  **Run SQL Query:** Construct the SQL query in {ctx.deps.db_engine.dialect.name} syntax based on the user's request and the table schemas. Aim to generate the correct query on the first attempt.
        *   **PostgreSQL Specifics:** If the database is PostgreSQL, use `EXTRACT(MONTH FROM column_name)` or `TO_CHAR(column_name, 'MM')` for month extraction, and `EXTRACT(YEAR FROM column_name)` or `TO_CHAR(column_name, 'YYYY')` for year extraction. DO NOT use `strftime`.
        *   Execute the query using the `run_sql_tool`. This tool will return a `SQLQueryResult` object containing the SQL query and its JSON results (or an error/empty array if no data).
    5.  **Analyze and Formulate Response:** After successfully running the SQL query and obtaining the `SQLQueryResult` object:
        a.  **Standard SQL Success:** Formulate a `SQLSuccess` response.
            *   The `detail` field should contain:
                - An explanation of the SQL query and the steps taken.
                - The SQL query that was executed.
                - The complete JSON string result from `run_sql_tool`. This JSON string should be presented clearly within a JSON markdown code block.
            *   The `query_results_json` field MUST contain the complete JSON string result from `run_sql_tool`. If the query yields no data, this field MUST be an empty JSON array (e.g., "[]").
            *   If at any stage an error occurs (e.g., `run_sql_tool` returns an error), explain this in the `detail` field of `SQLSuccess` and set `query_results_json` to an empty JSON array ("[]"), or use an `InvalidRequest` response if appropriate (e.g., user request is malformed).
    
    **Important Note on SQL Aliases and String Literals:**
    *   Avoid using reserved SQL keywords (like `as`, `from`, `where`, etc.) as unquoted aliases for tables or columns in your queries to prevent syntax errors. Use descriptive aliases or quote them if necessary.
    *   For string literals (e.g., values in a WHERE clause), ALWAYS use single quotes (e.g., `'Rock'`) and NEVER double quotes (e.g., `"Rock"`).
    """

@sql_query_creator_agent.tool
def list_tables_tool(ctx: RunContext[Dependencies]) -> str:
    print('list_tables_tool called')
    """Use this function to get a list of table names in the database. """
    return list_tables(ctx.deps.db_engine)

@sql_query_creator_agent.tool
def describe_table_tool(ctx: RunContext[Dependencies], table_name: str) -> str:
    print('describe_table_tool called', table_name)
    """Use this function to get a description of a table in the database."""
    return describe_table(ctx.deps.db_engine, table_name)

@sql_query_creator_agent.tool
def run_sql_tool(ctx: RunContext[Dependencies], query: str, limit: int = 10) -> str:
    print('run_sql_tool called', query)
    """Use this function to run a SQL query on the database. """
    return run_sql_query(ctx.deps.db_engine, query, limit)

@sql_query_creator_agent.output_validator
def sql_query_creator_agent_output_validator(ctx: RunContext[Dependencies], output: SQLResponse) -> SQLResponse:
    """
    Validates the parsed output object from the SQLAgent.
    This function is called by pydantic-ai after it attempts to parse the LLM's raw output
    into the specified output_type (SQLResponse).
    """
    if isinstance(output, InvalidRequest):
        # If pydantic-ai already determined it's an InvalidRequest, just return it.
        print(f"SQLAgent Result Validator: Received InvalidRequest: {output.error_message}")
        return output
    
    if isinstance(output, SQLSuccess):
        # Perform additional validation on the SQLSuccess object if needed.
        # For example, ensure critical fields are not empty or have expected formats.
        if not output.sql_query:
            print("SQLAgent Result Validator: SQLSuccess object has an empty sql_query.")
            return InvalidRequest(error_message="SQLSuccess object has an empty sql_query.")
        
        if not output.query_results_json:
            print("SQLAgent Result Validator: SQLSuccess object has an empty or missing query_results_json.")
            return InvalidRequest(error_message="SQLSuccess object has an empty or missing query_results_json. It must be a valid JSON string, even if empty (e.g., '[]').")

        print("SQLAgent Result Validator: SQLSuccess object passed custom validation.")
        return output