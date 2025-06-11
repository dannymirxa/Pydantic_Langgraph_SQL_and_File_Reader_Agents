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

load_dotenv("/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/.env")

# Initialize database engine
DATABASE_URL = "postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment" # Replace with your actual database URL
db_engine = create_engine(DATABASE_URL)

class MasterAgentResponse(BaseModel):
    response: Union[SQLResponse, FileResponse] = Field(description="The response from the chosen sub-agent.")

@dataclass
class MasterDependencies:
    db_engine: Engine
    available_files: list[str]

master_agent = Agent(
    model=OPENAI_MODEL,
    output_type=MasterAgentResponse,
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
    3. Call the appropriate tool (`run_sql_query_creator_agent` or `run_file_reader_agent`) with the user's original query.
    4. If the user's request is ambiguous or requires both, prioritize the most direct interpretation or ask for clarification if absolutely necessary (though try to avoid asking questions and make a decision).
    5. The output of the chosen sub-agent will be wrapped in a `MasterAgentResponse`.
    """

@master_agent.tool
def run_sql_query_creator_agent(ctx: RunContext[MasterDependencies], user_query: str) -> SQLResponse:
    """
    Use this tool to delegate a user's request to the SQL Query Creator Agent.
    This agent is suitable for requests involving database queries, table listing, or schema descriptions.
    Pass the user's original query directly to this tool.
    """
    print(f"Delegating to SQL Query Creator Agent with query: {user_query}")
    return sql_query_creator_agent.run_sync(user_query, deps=sql_query_creator.Dependencies(db_engine=ctx.deps.db_engine))

@master_agent.tool
def run_file_reader_agent(ctx: RunContext[MasterDependencies], user_query: str) -> FileResponse:
    """
    Use this tool to delegate a user's request to the File Reader Agent.
    This agent is suitable for requests involving reading content from specific files.
    Pass the user's original query directly to this tool.
    """
    print(f"Delegating to File Reader Agent with query: {user_query}")
    return file_reader_agent.run_sync(user_query, deps=file_reader.Dependencies(files=ctx.deps.available_files))


async def main():
    # Dynamically get available files
    files_directory = "/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/files"
    available_files = list_files(files_directory)

    # Example 1: SQL query
    sql_query_result = await master_agent.run(
        "Show me how many albums each artist has",
        deps=MasterDependencies(db_engine=db_engine, available_files=available_files)
    )

    # Example 2: File reading
    file_read_result = await master_agent.run(
        "What is in the bike data?",
        deps=MasterDependencies(db_engine=db_engine, available_files=available_files)
    )

    # Example 3: Ambiguous request (should ideally go to SQL if it mentions "data" and "tables")
    ambiguous_result = await master_agent.run(
        "For customers located in the USA, find the total sales amount for each customer. What is about risc?",
        deps=MasterDependencies(db_engine=db_engine, available_files=available_files)
    )
    
    return sql_query_result, file_read_result, ambiguous_result
# Example usage (for testing purposes)
if __name__ == "__main__":
    sql_response, file_read_response, generic_result = asyncio.run(main())
    # print(sql_response.output)
    # print(file_read_response.output)
    print(generic_result)

    # # Example 2: File reading
    # file_read_result = master_agent.run(
    #     "Read the content of the bike data file.",
    #     deps=MasterDependencies(db_engine=db_engine, available_files=available_files)
    # )
    # print("\n--- File Read Result ---")
    # print(file_read_result)

    # # Example 3: Ambiguous request (should ideally go to SQL if it mentions "data" and "tables")
    # ambiguous_result = master_agent.run(
    #     "I need sto know sales of albums by artist. I need to know also about risc",
    #     deps=MasterDependencies(db_engine=db_engine, available_files=available_files)
    # )
    # print("\n--- Ambiguous Request Result ---")
    # print(ambiguous_result)
