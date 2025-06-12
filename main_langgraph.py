from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import TypedDict, Annotated
from sqlalchemy import Engine, create_engine
from langchain_core.messages import HumanMessage

from agents import  sql_query_creator, file_reader, master
from agents.file_reader import file_reader_agent, FileSuccess
from agents.sql_query_creator import sql_query_creator_agent, SQLSuccess
from agents.master import ( 
                        master_agent, MasterAgentResponse,
                        SQL_AGENT,
                        FILE_AGENT,
                        BOTH_AGENT,
                        NONE
                        )
from util_functions.file_operations import list_files

load_dotenv()

# db_engine = create_engine('postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment')
# files = list_files(dir ="/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/files")

class AllState(TypedDict):
    # request: str
    request: Annotated[list[AnyMessage], add_messages]
    # db_engine: Engine = db_engine
    # files: list[str] = files
    db_engine: str
    files: str
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



def master_agent_node(state = AllState):
    master_agent_response = master_agent.run_sync(
        user_prompt=state["request"][-1].content,
        deps=master.MasterDependencies(db_engine=create_engine(state["db_engine"]), available_files=list_files(dir =state["files"]))
        )
    return {
        "agent": master_agent_response.output.agent
    }


def sql_query_creator_node(state: AllState):
    sql_query_agent_response = sql_query_creator_agent.run_sync(
        user_prompt=state["request"][-1].content,
        deps=sql_query_creator.Dependencies(db_engine=create_engine(state["db_engine"]))
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
        user_prompt=state["request"][-1].content,
        deps= file_reader.Dependencies(files=list_files(state["files"]))
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
    import json
    output_state = state.copy()
    if "db_engine" in output_state:
        del output_state["db_engine"]
    
    # Convert HumanMessage objects to their content strings for JSON serialization
    if "request" in output_state and isinstance(output_state["request"], list):
        output_state["request"] = [
            msg.content if hasattr(msg, 'content') else str(msg)
            for msg in output_state["request"]
        ]

    with open("checking_output.json", "w") as f:
        json.dump(output_state, f, indent=4)
    return state

def sql_or_output_router(state: AllState):
    if state["agent"] == BOTH_AGENT:
        return "sql_query_create_agent" # Start with SQL agent for both
    elif state["agent"] == SQL_AGENT:
        return "sql_query_create_agent"
    elif state["agent"] == FILE_AGENT:
        return "file_reader_agent"
    elif state["agent"] == NONE:
        return "end"
    else:
        return "end"

def after_sql_router(state: AllState):
    if state["agent"] == BOTH_AGENT:
        return "file_reader_agent"
    else: # This means it was originally SQL_AGENT
        return "output"
    
def create_graph():
    graph = StateGraph(AllState)

    graph.add_node("master", master_agent_node)
    graph.add_node("sql_query_create_agent", sql_query_creator_node)
    graph.add_node("file_reader_agent", file_reader_node)
    graph.add_node("output", output)

    graph.add_conditional_edges("master",
                                sql_or_output_router,
                                {
                                    "sql_query_create_agent": "sql_query_create_agent",
                                    "file_reader_agent": "file_reader_agent",
                                    "end": END
                                }
    )
    
    graph.add_conditional_edges("sql_query_create_agent",
                                after_sql_router,
                                {
                                    "file_reader_agent": "file_reader_agent", # If both, go to file reader
                                    "output": "output" # If only SQL, go to output
                                }
    )

    graph.add_edge("file_reader_agent", "output")
    graph.add_edge("output", END)

    graph.set_entry_point("master")

    return graph.compile()

graph = create_graph()

def main():

    

    from langchain_core.runnables.graph import MermaidDrawMethod

    graph_png = graph.get_graph().draw_mermaid_png(
        draw_method=MermaidDrawMethod.PYPPETEER,
    )

    initial_state = {
                        "request":
                            [HumanMessage(content="forget previous request, i need the crime data content")],
                        # "db_engine":
                        #     create_engine('postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment'),
                        # "files": 
                        #     list_files(dir ="/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/files")
                        "db_engine":
                           'postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment',
                        "files": 
                            "/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/files"
                    }

    with open("graph.png", "wb") as f:
        f.write(graph_png)

    for event in graph.stream(initial_state):
        for key in event:
            print("\n-----------------------------------")
            print("Done with " + key)
            print("\n*******************************************\n")

if  __name__ == "__main__":
    main()