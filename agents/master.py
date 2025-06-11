import sys
import asyncio
from dotenv import load_dotenv
from dataclasses import dataclass
from typing_extensions import Annotated, TypeAlias, Union, Optional
from annotated_types import MinLen
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext
from sqlalchemy import create_engine, Engine

from models import OPENAI_MODEL
from agents import  sql_query_creator, file_reader  
from agents.sql_query_creator import sql_query_creator_agent, SQLResponse
from agents.file_reader import file_reader_agent,  FileResponse
from util_functions.file_operations import list_files

# define which agent
SQL_AGENT = "sql_agent"
FILE_AGENT = "file_agent"
BOTH_AGENT = "both_agent"

class MasterAgentResponse(BaseModel):
    agent: str

@dataclass
class MasterDependencies:
    db_engine: Engine
    available_files: list[str]

master_agent = Agent(
    model=OPENAI_MODEL,
    output_type=MasterAgentResponse,
    result_tool_description="To decide which agent to use.",
    result_retries=3,
  )

@master_agent.system_prompt
def master_system_prompt(ctx: RunContext[MasterDependencies]) -> str:
    return f"""\
    You are a master AI agent designed to coordinate between a SQL query creator agent and a file reader agent.
    Your primary goal is to understand the user's request and delegate it to the appropriate sub-agent.

    Here are the available sub-agents and their capabilities:
    - **SQL Query Creator Agent:** Use this agent when the user's request involves querying a database.
      It can list tables, describe table schemas, and run SQL queries.
      Use the `run_sql_query_creator_agent` tool to interact with it.
      The database engine is already configured.

    - **File Reader Agent:** Use this agent when the user's request involves reading content from files.
      It can read JSON, CSV, text, and PDF files.
      Use the `run_file_reader_agent` tool to interact with it.
      The available files are dynamically retrieved from the 'files/' directory.

    **Instructions:**
    1. Analyze the user's request carefully.
    2. Determine whether the request is primarily about database interaction or file content reading.
    3. Give output between these options `{SQL_AGENT}` for `SQL Query Creator Agent` or `{FILE_AGENT}` for `File Reader Agent` with the user's original query.
    4. If the user's request clearly involves both database interaction (e.g., "sales", "customers", "products") AND file content reading (e.g., "document", "report", "file content"), give output `{BOTH_AGENT}`.
    5. If the user's request is ambiguous or requires both, prioritize the most direct interpretation or ask for clarification if absolutely necessary (though try to avoid asking questions and make a decision).
    5. The output of the chosen sub-agent will be wrapped in a `MasterAgentResponse`.

    Only choose from these options: `{SQL_AGENT}`, `{FILE_AGENT}`, or `{BOTH_AGENT}`"
    """

@master_agent.output_validator
def validate_result(ctx: RunContext[None], response: MasterAgentResponse) -> MasterAgentResponse:
    if response.agent not in [SQL_AGENT, FILE_AGENT, BOTH_AGENT]:
        raise ModelRetry(
            f"Invalid action. Please choose from `{SQL_AGENT}`, `{FILE_AGENT}`, or `{BOTH_AGENT}``"
        )

    return response