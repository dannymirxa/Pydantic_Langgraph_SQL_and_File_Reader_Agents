
from dataclasses import dataclass
from sqlalchemy import Engine, create_engine
from agents.file_reader import file_reader_agent
from agents.sql_query_creator import sql_query_creator_agent
from util_functions.file_operations import list_files

import asyncio


@dataclass
class Dependencies:
    # db_engine: Engine
    files: list[str]



async def main(request: str):

    # db_engine = create_engine('postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment')

    # deps = Dependencies(db_engine=db_engine)

    # sql_agent_response = await sql_query_creator_agent.run(user_prompt=request,
    #                                                        deps=deps)
    
    # return sql_agent_response
    file = list_files(dir ="/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/files")

    deps = Dependencies(files=file)
    
    file_reader_agent_response = await file_reader_agent.run(user_prompt=request,
                                                                     deps=deps)
    
    return file_reader_agent_response

    
if  __name__ == '__main__':
    
    file_response = asyncio.run(main("I want to know about bike data"))
    print(file_response.output)