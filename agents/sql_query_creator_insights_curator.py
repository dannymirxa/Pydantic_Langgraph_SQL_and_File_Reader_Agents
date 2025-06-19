import sys

# adding Folder_2 to the system path
# sys.path.insert(0, 'utils')
from util_functions.sql_operations import list_tables, describe_table, run_sql_query
from models import OPENAI_MODEL

from agents import insights_curator
from agents.insights_curator import data_insights_agent, DataframeSuccess, InsightsError, DataframeResponse

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
                               InvalidRequest,
                               DataframeResponse
                               ]

@dataclass
class Dependencies:
    db_engine: Engine
    sql_query: str | None = None

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
    4.  **Run SQL Query:** Construct the SQL query in Postgres syntax based on the user's request and the table schemas. Execute it using the `run_sql_tool`. This tool will return a `SQLQueryResult` object containing the SQL query and its JSON results (or an error/empty array if no data).
    5.  **Analyze and Formulate Response:** After successfully running the SQL query and obtaining the `SQLQueryResult` object:
        a.  **Attempt Dataframe Creation and Insights:** If the user's request implies a need for data insights (e.g., "analyze", "trends", "summary", "insights", "chart"), or if the SQL query result is suitable for DataFrame conversion, call the `run_insights_curator_agent` tool with the `sql_query`, `detail`, and `query_results_json` from the `SQLQueryResult` object.
            *   If `run_insights_curator_agent` returns a `DataframeSuccess` object, return this object directly as your final response.
            *   If `run_insights_curator_agent` returns an `InsightsError`, explain the error in the `detail` field of a `SQLSuccess` object, or return an `InvalidRequest` if the error is due to a malformed user request.
        b.  **Standard SQL Success:** If insights are not requested or cannot be generated, formulate a `SQLSuccess` response.
            *   The `detail` field should still contain:
                - An explanation of the SQL query and the steps taken.
                - The SQL query that was executed.
                - The complete JSON string result from `run_sql_tool`. This JSON string should be presented clearly within a JSON markdown code block.
            *   If at any stage an error occurs (e.g., `run_sql_tool` returns an error) or a query yields no data (after `run_sql_tool`), explain this in the `detail` field of `SQLSuccess` or use an `InvalidRequest` response if appropriate (e.g., user request is malformed).
    
    **Important Note on SQL Aliases:** Avoid using reserved SQL keywords (like `as`, `from`, `where`, etc.) as unquoted aliases for tables or columns in your queries to prevent syntax errors. Use descriptive aliases or quote them if necessary.
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

@sql_query_creator_agent.tool
def run_insights_curator_agent(ctx: RunContext[Dependencies], sql_query: str, detail: str, query_results_json: str):
    print('run_insights_curator_agent called')
    
    return data_insights_agent.run_sync(deps=insights_curator.Dependencies(sql_query=sql_query, detail=detail, query_results_json=query_results_json))

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
        
        print("SQLAgent Result Validator: SQLSuccess object passed custom validation.")
        return output
    elif isinstance(output, DataframeResponse):
        # DataframeResponse objects do not have a sql_query attribute, so no need to validate it here.
        print("SQLAgent Result Validator: DataframeResponse object passed custom validation.")
        return output
