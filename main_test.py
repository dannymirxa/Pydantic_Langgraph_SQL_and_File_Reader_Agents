
from dataclasses import dataclass
from sqlalchemy import Engine, create_engine
from agents.file_reader import file_reader_agent, FileSuccess
# from agents.sql_query_creator_insights_curator import sql_query_creator_agent
from agents.sql_query_creator import sql_query_creator_agent
from agents.insights_curator import data_insights_agent
from agents.master import master_agent, MasterDependencies
from agents.chart_generator import chart_creator_agent
from util_functions.file_operations import list_files

from typing_extensions import Optional
import asyncio


@dataclass
class Dependencies:
    # db_engine: Engine
    # files: list[str]
    sql_query: Optional[str]
    detail: Optional[str]
    query_results_json: str

async def main(request: str):

    db_engine = create_engine('postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment')

    deps = Dependencies(
                        # db_engine=db_engine, 
                        sql_query="SELECT artist.name AS artist_name, SUM(invoice_line.unit_price * invoice_line.quantity) AS total_sales FROM artist JOIN album ON artist.artist_id = album.artist_id JOIN track ON album.album_id = track.album_id JOIN invoice_line ON track.track_id = invoice_line.track_id GROUP BY artist.name ORDER BY total_sales DESC;",
                        detail= None,
                        query_results_json= """[
	{
		"artist_name": "U2",
		"sales_count": 91
	},
	{
		"artist_name": "Led Zeppelin",
		"sales_count": 87
	},
	{
		"artist_name": "Iron Maiden",
		"sales_count": 54
	},
	{
		"artist_name": "Deep Purple",
		"sales_count": 44
	},
	{
		"artist_name": "Queen",
		"sales_count": 37
	},
	{
		"artist_name": "Creedence Clearwater Revival",
		"sales_count": 37
	},
	{
		"artist_name": "Kiss",
		"sales_count": 31
	},
	{
		"artist_name": "Van Halen",
		"sales_count": 29
	},
	{
		"artist_name": "Pearl Jam",
		"sales_count": 26
	},
	{
		"artist_name": "Guns N' Roses",
		"sales_count": 26
	}
]"""
                        )

    # sql_agent_response = await sql_query_creator_agent.run(user_prompt=request,
    #                                                        deps=deps)
    
    # return sql_agent_response
    # file = list_files(dir ="/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/files")

    # deps = MasterDependencies(db_engine=db_engine, available_files=file)
    
    # file_reader_agent_response = await master_agent.run(user_prompt=request,
    #                                                                  deps=deps)
    
    # return file_reader_agent_response

    # data_insights_agent_response = await data_insights_agent.run(user_prompt=request,
    #                                                               deps=deps)
    
    # return data_insights_agent_response

    chart_agent_response = await chart_creator_agent.run(user_prompt=request,
                                                          deps=deps)

    return chart_agent_response
    
if  __name__ == '__main__':
    
    file_response = asyncio.run(main("I  want to know the total sales by artist in vertical and horizontal bar charts"))
    # file_response = asyncio.run(main("Need to know about total album sales by artist"))
    # file_response = asyncio.run(main("create insights from given dataframe"))
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