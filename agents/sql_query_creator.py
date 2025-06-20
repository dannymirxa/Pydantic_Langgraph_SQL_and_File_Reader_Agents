import sys

# adding Folder_2 to the system path
# sys.path.insert(0, 'utils')
from util_functions.sql_operations import list_tables, describe_table, run_sql_query
from models import OPENAI_MODEL, SQLSuccessWithInsights

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
    
class InvalidRequest(BaseModel):
    error_message: str

SQLResponse: TypeAlias = Union[
                                SQLSuccess, 
                               InvalidRequest, 
                               SQLSuccessWithInsights]

@dataclass
class Dependencies:
    db_engine: Engine

sql_query_creator_agent = Agent(
    model=OPENAI_MODEL,
    output_type=SQLResponse,
    result_retries=3,
)

@sql_query_creator_agent.system_prompt
def system_prompt() -> str:
    return f"""\
    You are an AI agent equipped with database tools. Your goal is to help users interact with a database by generating and executing SQL queries, and if requested, facilitate chart generation.

    Follow these steps meticulously:
    1.  **List Tables:** If you need to know the available tables, use the `list_tables_tool`.
    2.  **Describe Table:** To understand the schema of specific table(s) relevant to the user's request, use the `describe_table_tool` for each of them.
    3.  **Handle Sales/Revenue Queries:** If the user's request involves "sales", "revenue", or "total amount", remember that this data is typically derived from the `invoice_line` table (which has `unit_price` and `quantity`). You will likely need to join `artist`, `album`, `track`, and `invoice_line` tables to fulfill such requests. Calculate sales as `SUM(invoice_line.unit_price * invoice_line.quantity)`.
    4.  **Run SQL Query:** Construct the SQL query in Postgres syntax based on the user's request and the table schemas. Execute it using the `run_sql_tool`. This tool will return a JSON string of the query results (or an error/empty array if no data).
    5.  **Analyze and Formulate Response (SQLSuccessWithInsights):** After successfully running the SQL query and obtaining the JSON result, analyze the data to extract meaningful insights.
        a.  **Data Analysis:**
            -   Identify key metrics (e.g., sums, averages, counts, min/max values).
            -   Look for trends over time (if date columns are present).
            -   Identify top N or bottom N items.
            -   Note any significant distributions or outliers.
            -   Consider the user's original request to focus insights on their intent.
        b.  **Insight Generation:** Populate the `data_insights` field with concise, clear, and actionable observations from the data. Each insight should be a separate string in the list.
        c.  **Chart Suggestions:** Based on the data and insights, suggest appropriate chart types and the columns that should be used for X-axis, Y-axis, and series. Populate the `chart_suggestions` field.
        d.  The `detail` field should still contain:
            - An explanation of the SQL query and the steps taken.
            - The SQL query that was executed.
            - The complete JSON string result from `run_sql_tool`. This JSON string should be presented clearly within a JSON markdown code block.
        e. If at any stage an error occurs (e.g., `run_sql_tool` returns an error) or a query yields no data (after `run_sql_tool`), explain this in the `detail` field of `SQLSuccess` or use an `InvalidRequest` response if appropriate (e.g., user request is malformed).
    
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
    
    if isinstance(output, (SQLSuccess, SQLSuccessWithInsights)):
        # Perform additional validation on the SQLSuccess or SQLSuccessWithInsights object if needed.
        # For example, ensure critical fields are not empty or have expected formats.
        if not output.sql_query:
            print("SQLAgent Result Validator: SQLSuccess/SQLSuccessWithInsights object has an empty sql_query.")
            return InvalidRequest(error_message="SQLSuccess/SQLSuccessWithInsights object has an empty sql_query.")
        
        print("SQLAgent Result Validator: SQLSuccess/SQLSuccessWithInsights object passed custom validation.")
        return output
