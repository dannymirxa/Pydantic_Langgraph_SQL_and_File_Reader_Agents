from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict
from sqlalchemy import create_engine

from agents import  sql_query_creator, file_reader, master
from agents.file_reader import file_reader_agent, FileSuccess
from agents.sql_query_creator import sql_query_creator_agent, SQLSuccess
from agents.master import ( 
                        master_agent, MasterAgentResponse,
                        SQL_AGENT,
                        FILE_AGENT,
                        BOTH_AGENT
                        )
from util_functions.file_operations import list_files

load_dotenv()

class AllState(TypedDict):
    request: str
    agent: str
    sql_query: str | None
    detail: str | None
    sql_error_message: str | None
    file_content: str | None
    summary: str | None
    file_error_message: str | None

class FileReaderState(TypedDict):
    request: str
    error_message: str | None = None

db_engine = create_engine('postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment')
files = list_files(dir ="/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/files")

def master_agent_node(state = AllState):
    master_agent_response = master_agent.run_sync(
        user_prompt=state["request"], 
        deps=master.MasterDependencies(db_engine=db_engine, available_files=files))
    return {
        "agent": master_agent_response.output.agent
    }


def sql_query_creator_node(state: AllState):
    sql_query_agent_response = sql_query_creator_agent.run_sync(
        user_prompt=state["request"], 
        deps=sql_query_creator.Dependencies(db_engine=db_engine)
        )
    
    if isinstance(sql_query_agent_response.output, SQLSuccess):
        return {
            "sql_query": sql_query_agent_response.output.sql_query,
            "detail": sql_query_agent_response.output.sql_query,
        }
    
    else: 
        return {
            "sql_error_message": sql_query_agent_response.output.error_message
        }


def file_reader_node(state: AllState):
    file_reader_agent_response = file_reader_agent.run_sync(
        user_prompt=state["request"], 
        deps= file_reader.Dependencies(files=files)
        )
    
    if isinstance(file_reader_agent_response.output, FileSuccess):
        return {
            "file_content": file_reader_agent_response.output.file_content,
            "summary": file_reader_agent_response.output.summary,
        }
    else:
        return {
            "file_error_message": file_reader_agent_response.output.error_message
        }

def output(state: AllState):
    print(state)
    return state

def router(state: AllState):
    if state["agent"] == "both_agent":
        return "both_agent"
    elif state["agent"] == "sql_agent":
        return "sql_agent"
    elif state["agent"] == "file_agent":
        return "file_agent"
    else:
        return "end"
    
def create_graph():
    graph = StateGraph(AllState)

    graph.add_node("master", master_agent_node)
    graph.add_node("sql_query_create_agent", sql_query_creator_node)
    graph.add_node("file_reader_agent", file_reader_node)
    graph.add_node("output", output)

    graph.add_conditional_edges("master", 
                                router,
                                { 
                                    "both_agent": "both_agent", 
                                    "sql_agent": "sql_agent", 
                                    "file_agent": "file_agent", 
                                    "end": END
                                }
    )
    
    graph.add_edge("master", "router")
    graph.add_edge("both_agent", "sql_query_create_agent")
    graph.add_edge("both_agent", "file_reader_agent")
    graph.add_edge("sql_agent", "sql_query_create_agent")
    graph.add_edge("file_agent", "file_reader_agent")
    graph.add_edge("sql_query_create_agent", "output")
    graph.add_edge("file_reader_agent", "output")
    graph.add_edge("output", END)

    graph.set_entry_point("master")

    return graph.compile()

def main():

    graph = create_graph()

    from langchain_core.runnables.graph import MermaidDrawMethod

    graph_png = graph.get_graph().draw_mermaid_png(
        draw_method=MermaidDrawMethod.PYPPETEER,
    )

    with open("graph.png", "wb") as f:
        f.write(graph_png)

if  __name__ == "__main__":
    main()