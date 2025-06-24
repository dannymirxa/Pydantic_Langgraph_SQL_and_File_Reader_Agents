# Pydantic-Langgraph SQL and File Reader Agents

This project demonstrates a multi-agent system built using Pydantic-AI and Langchain, designed to intelligently delegate user requests to specialized sub-agents for SQL querying and file reading. The system is highly flexible and extensible, making it suitable for various data interaction tasks.

## Project Overview

The core of this project is a `MasterAgent` that acts as a coordinator, analyzing user queries and routing them to either a `SQL Query Creator Agent` or a `File Reader Agent`. This allows for a flexible and extensible system capable of handling diverse data interaction requests.

## Architecture

The system is composed of the following key components:

1. **`MasterAgent`**: The central orchestrator. It receives user requests, determines the intent (SQL query, file reading, or both), and delegates the task to the appropriate sub-agent.
2. **`SQL Query Creator Agent`**: Specializes in interacting with a PostgreSQL database. It can list tables, describe table schemas, and execute SQL queries.
3. **`File Reader Agent`**: Specializes in reading and summarizing content from various file types (JSON, CSV, TXT, PDF).
4. **`Insights Curator Agent`**: Specializes in generating data insights from SQL query results.
5. **`Chart Generator Agent`**: Specializes in generating Python code for data visualizations (charts) based on query results.
6. **`Models`**: Defines the Pydantic models for input/output types and the OpenAI model configuration.
7. **`Utility Functions`**: Provides helper functions for file operations (listing, reading various formats) and SQL operations (listing tables, describing tables, running queries).

### Detailed Architecture

- **MasterAgent**: Acts as the brain of the system, interpreting user requests and deciding which sub-agent to delegate the task to. It uses a system prompt to guide its decision-making process.
- **SQL Query Creator Agent**: Handles all interactions with the PostgreSQL database. It can list available tables, describe table schemas, and execute SQL queries. It provides detailed explanations of the queries and their results.
- **File Reader Agent**: Handles reading and summarizing content from various file types. It validates the existence of the requested file, determines the file type, and uses the appropriate tool to read the content.
- **Insights Curator Agent**: Processes SQL query results (as DataFrames) to extract key insights and suggest further analytical questions.
- **Chart Generator Agent**: Takes processed data and user requests to generate Plotly Python code for various chart types, saving them as HTML files.
- **Models**: Defines the data structures used for input and output. This includes models for user requests, SQL responses, file responses, insights, chart code, and error handling.
- **Utility Functions**: Provides common functions for file and SQL operations. These functions are used by the agents to perform their tasks.

## Agents

### Master Agent (`agents/master.py` and `main.py`)

<img src="graph.png" style="width:500px;">

The `MasterAgent` is responsible for intelligent routing.

- **Purpose**: To understand the user's request and delegate it to the appropriate sub-agent.
- **System Prompt**: Guides the agent to analyze the request, identify keywords related to SQL or file operations, and choose the correct sub-agent. It also handles cases where files are not found.
- **Tools**:
  - `run_sql_query_creator_agent`: Delegates the query to the SQL agent.
  - `run_file_reader_agent`: Delegates the query to the File Reader agent.
- **Output Type**: `MasterAgentResponse` which wraps either a `SQLResponse` or a `FileResponse`.

### SQL Query Creator Agent (`agents/sql_query_creator.py`)

<img src="graphs/sql_query_create_agent.png" style="width:500px;">

This agent handles all database interactions.

- **Purpose**: To generate and execute SQL queries based on user requests.
- **System Prompt**: Instructs the agent to first list tables, then describe relevant tables, and finally construct and run the SQL query. It emphasizes providing a detailed explanation of the query and its results.
- **Tools**:
  - `list_tables_tool()`: Lists all available tables in the connected database.
  - `describe_table_tool(table_name: str)`: Provides the schema for a specified table.
  - `run_sql_tool(query: str, limit: int = 10)`: Executes a given SQL query and returns the results.
- **Output Type**: `SQLResponse` (Union of `SQLSuccess` or `InvalidRequest`).

### File Reader Agent (`agents/file_reader.py`)

This agent handles reading content from various file types.

- **Purpose**: To read and summarize content from specified files.
- **System Prompt**: Guides the agent to first validate if the requested file exists in the provided list of available files. If found, it determines the file type and calls the appropriate reading tool.
- **Tools**:
  - `read_json_tool(file_path: str)`: Reads and summarizes JSON files.
  - `read_csv_tool(file_path: str)`: Reads and summarizes CSV files.
  - `read_text_tool(file_path: str)`: Reads and summarizes plain text files.
  - `read_pdf_tool(file_path: str)`: Reads and summarizes PDF files.
- **Output Type**: `FileResponse` (Union of `FileSuccess` or `InvalidRequest`).

### Insights Curator Agent (`agents/insights_curator.py`)

This agent focuses on extracting meaningful insights from data.

- **Purpose**: To analyze query results (provided as a Pandas DataFrame) and generate key data insights and analytical questions.
- **System Prompt**: Guides the agent to obtain DataFrame metadata, analyze it, and then generate a brief description of the dataset and 8-10 actionable data analysis questions.
- **Tools**:
  - `create_dataframe_pd_tool()`: Creates a Pandas DataFrame from JSON query results and returns its metadata (rows, columns, data types, missing values).
- **Output Type**: `DataframeSuccess` (containing a list of insights) or `InsightsError`.

### Chart Generator Agent (`agents/chart_generator.py`)

This agent is responsible for visualizing data.

- **Purpose**: To generate Plotly Python code for various chart types based on user requests and query results.
- **System Prompt**: Instructs the agent to analyze the user's request and the provided DataFrame, adhere to requested chart types (if suitable), generate insights, and produce executable Plotly Python code. It emphasizes saving charts as HTML files (e.g., `templates/chart_0.html`) and *not* using `fig.show()`.
- **Output Type**: `ChartSuccess` (containing a list of Python code strings) or `ChartError`.

## Models (`models.py`)

- `OPENAI_MODEL`: Configures the OpenAI model (`gpt-4o`) used by the agents, including Azure OpenAI specific settings.
- `Request`: A Pydantic model for general user queries.
- `SQLSuccess`: Represents a successful SQL query execution, including the query and a detailed explanation/result.
- `FileSuccess`: Represents successful file content retrieval, including the content and a summary.
- `InvalidRequest`: A common model used across agents to indicate an error or an invalid request.
- `DataframeSuccess`: Represents successful data insights generation, including the SQL query, detail, query results, and a list of data insights.
- `InsightsError`: Indicates an error during insights generation.
- `ChartSuccess`: Represents successful chart code generation, including a list of Python code strings.
- `ChartError`: Indicates an error during chart generation.

## Utility Functions

### `util_functions/file_operations.py`

- `list_files(directory: str)`: Lists files within a specified directory.
- `read_json(file_path: str)`: Reads and extracts content/summary from a JSON file.
- `read_csv(file_path: str)`: Reads and extracts content/summary from a CSV file.
- `read_txt(file_path: str)`: Reads and extracts content/summary from a TXT file.
- `read_pdf(file_path: str)`: Reads and extracts content/summary from a PDF file.

### `util_functions/sql_operations.py`

- `list_tables(engine: Engine)`: Lists tables in the database.
- `describe_table(engine: Engine, table_name: str)`: Describes the schema of a given table.
- `run_sql_query(engine: Engine, query: str, limit: int)`: Executes a SQL query and returns results.

## Setup and Running

### Prerequisites

- Python 3.9+
- Poetry (recommended for dependency management)
- PostgreSQL database (e.g., `chinook` database)
- OpenAI API Key (or Azure OpenAI credentials)
- Logfire Token (optional, for observability)

### Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/Pydantic_Langgraph_SQL_and_File_Reader_Agents.git
    cd Pydantic_Langgraph_SQL_and_File_Reader_Agents
    ```
2. **Install dependencies**:
    ```bash
    poetry install
    ```
3. **Environment Variables**: Create a `.env` file in the root directory and add your credentials:
    ```
    OPENAI_API_KEY="your_openai_api_key"
    AZURE_OPENAI_KEY="your_azure_openai_key"
    LOGFIRE_TOKEN="your_logfire_token" # Optional
    ```
    Adjust the `DATABASE_URL` in `main.py` to point to your PostgreSQL instance.
    ```python
    DATABASE_URL = "postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment"
    ```

### Running the Application

The `main_langgraph.py` script contains examples of how to use the `MasterAgent` within a LangGraph setup.

To run the examples:

```bash
poetry run python main.py
```

You can modify the `main` function in `main_langgraph.py` to test different user requests.

```python
```python
async def main(request: str):
    # Dynamically get available files
    files_directory = "/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/files"
    available_files = list_files(files_directory)

    # Example: Run a custom request
    result = await master_agent.run(
        request,
        deps=MasterDependencies(db_engine=db_engine, available_files=available_files)
    )
    return result

if __name__ == "__main__":
    # Example usage (for testing purposes)
    response = asyncio.run(main("Show me how many albums each artist has"))
    print(response.output)

    response = asyncio.run(main("What is in the bike data?"))
    print(response.output)

    response = asyncio.run(main("forget previous request, i wanted to know the average number of album sales by artists"))
    print(response.output)
```

The `graphs/sql_insights_charts.py` script demonstrates a more advanced LangGraph setup that integrates SQL querying, data insights, and chart generation.

To run this advanced example:

```bash
poetry run python graphs/sql_insights_charts.py
```

You can modify the `initial_state` in the `main` function of `graphs/sql_insights_charts.py` to test different user requests, including those that involve generating insights and charts.

```python
initial_state = {
    "request": [HumanMessage(content="I want to know how many sales of albums each artist with at least one rock genre. I want to create insights and the data visualized in 1. bar chart, 2. scatter plot and 3. line chart. ")],
    "db_engine": 'postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment',
    "files": "/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/files"
}
```
```

### Troubleshooting

- **Database Connection Issues**: Ensure that your PostgreSQL instance is running and that the `DATABASE_URL` is correctly configured.
- **API Key Errors**: Verify that your OpenAI API key or Azure OpenAI credentials are correctly set in the `.env` file.
- **Dependency Issues**: Ensure that all dependencies are installed correctly using Poetry. If issues persist, try running `poetry update`.

### Common Issues

- **File Not Found**: Ensure that the file paths provided in requests are correct and that the files exist in the specified directory.
- **Invalid Requests**: Ensure that the requests are correctly formatted and that the required parameters are provided.

## Usage Examples

Here are some examples of how to use the application with `main_langgraph.py`:

1. **SQL Query Example**:
    ```python
    response = asyncio.run(main("Show me how many albums each artist has"))
    print(response.output)
    ```

2. **File Reading Example**:
    ```python
    response = asyncio.run(main("What is in the bike data?"))
    print(response.output)
    ```

3. **Complex Request Example**:
    ```python
    response = asyncio.run(main("forget previous request, i wanted to know the average number of album sales by artists"))
    print(response.output)
    ```

And here's an example demonstrating the advanced capabilities with `graphs/sql_insights_charts.py`, including insights and chart generation:

```python
initial_state = {
    "request": [HumanMessage(content="I want to know how many sales of albums each artist with at least one rock genre. I want to create insights and the data visualized in 1. bar chart, 2. scatter plot and 3. line chart. ")],
    "db_engine": 'postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment',
    "files": "/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/files"
}
# To run this, you would typically use:
# for event in graph.stream(initial_state):
#     for key in event:
#         print("\n-----------------------------------")
#         print("Done with " + key)
#         print("\n*******************************************\n")
# graph.invoke(initial_state)
```

These examples demonstrate how to interact with the `MasterAgent` and the integrated LangGraph for SQL queries, file content reading, data insights, and chart generation. You can modify the requests to suit your specific needs.