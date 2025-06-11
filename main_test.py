
from dataclasses import dataclass
from sqlalchemy import Engine, create_engine
from agents.file_reader import file_reader_agent, FileSuccess
from agents.sql_query_creator import sql_query_creator_agent
from agents.master import master_agent, MasterDependencies
from util_functions.file_operations import list_files

import asyncio


@dataclass
class Dependencies:
    db_engine: Engine
    files: list[str]



async def main(request: str):

    db_engine = create_engine('postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment')

    # deps = Dependencies(db_engine=db_engine)

    # sql_agent_response = await sql_query_creator_agent.run(user_prompt=request,
    #                                                        deps=deps)
    
    # return sql_agent_response
    file = list_files(dir ="/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/files")

    deps = MasterDependencies(db_engine=db_engine, available_files=file)
    
    file_reader_agent_response = await master_agent.run(user_prompt=request,
                                                                     deps=deps)
    
    return file_reader_agent_response

    
if  __name__ == '__main__':
    
    # file_response = asyncio.run(main("I want to know how many sales of albums each artist with at least one rock genre"))
    file_response = asyncio.run(main("Need to know about total album sales by artist and generic agent docs"))
    print("-------Output-------")
    print(file_response.output)
    # print(file_response.output.sql_query)
    # print(file_response.output.detail)


    # print(file_response.output.file_content)
    # if isinstance(file_response.output, FileSuccess):
    #     summary = file_response.output.summary
    # else:
    #     summary = None
    # print(summary)
    # print(file_response.output)