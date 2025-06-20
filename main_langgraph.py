from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import TypedDict, Annotated, Optional
from sqlalchemy import Engine, create_engine
from langchain_core.messages import HumanMessage

from agents import  sql_query_creator, file_reader, master, insights_curator, chart_generator
from agents.file_reader import file_reader_agent, FileSuccess
from agents.sql_query_creator import sql_query_creator_agent, SQLSuccess
from agents.insights_curator import data_insights_agent, DataframeSuccess
from agents.chart_generator import chart_creator_agent, ChartSuccess

from agents.master import (
                        master_agent, MasterAgentResponse,
                        SQL_AGENT,
                        FILE_AGENT,
                        BOTH_AGENT,
                        NONE
                        )
from util_functions.file_operations import list_files
from models import ChartSuggestion

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
    sql_query: Optional[str]
    detail: Optional[str]
    query_results_json: Optional[str]
    sql_error_message: Optional[str]
    data_insights: Optional[list[str]]
    insights_error: Optional[str]
    python_codes: Optional[list[str]]
    chart_error: str 

    insights_error: Optional[str]
    file_content: Optional[str]
    summary: Optional[str]
    file_error_message: Optional[str]

class FileReaderState(TypedDict):
    request: str
    error_message: Optional[str] = None

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
            "detail": sql_query_agent_response.output.detail,
            "query_results_json": sql_query_agent_response.output.query_results_json,
        }
    else: # InvalidRequest
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
    
def data_insights_node(state: AllState):
    data_insights_agent_response = data_insights_agent.run_sync(
        deps=insights_curator.Dependencies( sql_query= state["sql_query"],
                                            detail= state["detail"],
                                            query_results_json= state["query_results_json"]
                                            )
        )
    
    if isinstance(data_insights_agent_response.output, DataframeSuccess):
        return {
            "data_insights": data_insights_agent_response.output.data_insights,
        }
    else: # InvalidRequest
        return {
            "insights_error": data_insights_agent_response.output.error_message
        }        
    
def chart_generator_node(state: AllState):
    chart_creator_response = chart_creator_agent.run_sync(
                user_prompt=state["request"][-1].content,
                deps=chart_generator.Dependencies(  query_results_json= state["query_results_json"]
                )
    )
    
    if isinstance(chart_creator_response.output, ChartSuccess):
        return {
            "python_codes": chart_creator_response.output.python_codes,
        }
    else: # InvalidRequest
        return {
            "chart_error": chart_creator_response.output.error_message
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
        return "data_insights_agent"
    
def after_sql_router(state: AllState):
    # If the master agent decided on a SQL path (SQL_AGENT or BOTH_AGENT),
    # we always want to proceed to data insights first.
    return "data_insights_agent"

def after_chart_router(state: AllState):
    if state["agent"] == BOTH_AGENT:
        return "file_reader_agent"
    else:
        return "output"

def create_graph():
    graph = StateGraph(AllState)

    graph.add_node("master", master_agent_node)
    graph.add_node("sql_query_create_agent", sql_query_creator_node)
    graph.add_node("file_reader_agent", file_reader_node)
    graph.add_node("output", output)
    graph.add_node("data_insights_agent", data_insights_node)
    graph.add_node("chart_generator_agent", chart_generator_node)

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
                                    "data_insights_agent": "data_insights_agent" # If only SQL, go to output
                                }
    )

    graph.add_conditional_edges("chart_generator_agent",
                                after_chart_router,
                                {
                                    "file_reader_agent": "file_reader_agent",
                                    "output": "output"
                                }
    )

    graph.add_edge("file_reader_agent", "output") # This edge is still needed for the file reader path
    graph.add_edge("data_insights_agent", "chart_generator_agent")
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
                            [HumanMessage(content="I want to know how many sales of albums each artist with at least one rock genre. I want to create insights and the data visualized in bar chart and scatter plot")],
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