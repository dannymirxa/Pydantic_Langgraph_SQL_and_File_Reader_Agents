# Pydantic-Langgraph SQL and File Reader Agents

This project demonstrates a multi-agent system built using Pydantic-AI and Langchain, designed to intelligently delegate user requests to specialized sub-agents for SQL querying and file reading.

## Project Overview

The core of this project is a `MasterAgent` that acts as a coordinator, analyzing user queries and routing them to either a `SQL Query Creator Agent` or a `File Reader Agent`. This allows for a flexible and extensible system capable of handling diverse data interaction requests.

## Architecture

The system is composed of the following key components:

1.  **`MasterAgent`**: The central orchestrator. It receives user requests, determines the intent (SQL query, file reading, or both), and delegates the task to the appropriate sub-agent.
2.  **`SQL Query Creator Agent`**: Specializes in interacting with a PostgreSQL database. It can list tables, describe table schemas, and execute SQL queries.
3.  **`File Reader Agent`**: Specializes in reading and summarizing content from various file types (JSON, CSV, TXT, PDF).
4.  **`Models`**: Defines the Pydantic models for input/output types and the OpenAI model configuration.
5.  **`Utility Functions`**: Provides helper functions for file operations (listing, reading various formats) and SQL operations (listing tables, describing tables, running queries).

## Agents

### Master Agent (`agents/master.py` and `main.py`)

The `MasterAgent` is responsible for intelligent routing.

*   **Purpose**: To understand the user's request and delegate it to the appropriate sub-agent.
*   **System Prompt**: Guides the agent to analyze the request, identify keywords related to SQL or file operations, and choose the correct sub-agent. It also handles cases where files are not found.
*   **Tools**:
    *   `run_sql_query_creator_agent`: Delegates the query to the SQL agent.
    *   `run_file_reader_agent`: Delegates the query to the File Reader agent.
*   **Output Type**: `MasterAgentResponse` which wraps either a `SQLResponse` or a `FileResponse`.

### SQL Query Creator Agent (`agents/sql_query_creator.py`)

This agent handles all database interactions.

*   **Purpose**: To generate and execute SQL queries based on user requests.
*   **System Prompt**: Instructs the agent to first list tables, then describe relevant tables, and finally construct and run the SQL query. It emphasizes providing a detailed explanation of the query and its results.
*   **Tools**:
    *   `list_tables_tool()`: Lists all available tables in the connected database.
    *   `describe_table_tool(table_name: str)`: Provides the schema for a specified table.
    *   `run_sql_tool(query: str, limit: int = 10)`: Executes a given SQL query and returns the results.
*   **Output Type**: `SQLResponse` (Union of `SQLSuccess` or `InvalidRequest`).

### File Reader Agent (`agents/file_reader.py`)

This agent handles reading content from various file types.

*   **Purpose**: To read and summarize content from specified files.
*   **System Prompt**: Guides the agent to first validate if the requested file exists in the provided list of available files. If found, it determines the file type and calls the appropriate reading tool.
*   **Tools**:
    *   `read_json_tool(file_path: str)`: Reads and summarizes JSON files.
    *   `read_csv_tool(file_path: str)`: Reads and summarizes CSV files.
    *   `read_text_tool(file_path: str)`: Reads and summarizes plain text files.
    *   `read_pdf_tool(file_path: str)`: Reads and summarizes PDF files.
*   **Output Type**: `FileResponse` (Union of `FileSuccess` or `InvalidRequest`).

## Models (`models.py`)

*   `OPENAI_MODEL`: Configures the OpenAI model (`gpt-4o`) used by the agents, including Azure OpenAI specific settings.
*   `Request`: A Pydantic model for general user queries.
*   `ChartResponses`: A Pydantic model for insights and Python code for plotting graphs (though charting functionality is not fully implemented in the provided `main.py`).
*   `SQLSuccess`: Represents a successful SQL query execution, including the query and a detailed explanation/result.
*   `FileSuccess`: Represents successful file content retrieval, including the content and a summary.
*   `InvalidRequest`: A common model used across agents to indicate an error or an invalid request.

## Utility Functions

### `util_functions/file_operations.py`

*   `list_files(directory: str)`: Lists files within a specified directory.
*   `read_json(file_path: str)`: Reads and extracts content/summary from a JSON file.
*   `read_csv(file_path: str)`: Reads and extracts content/summary from a CSV file.
*   `read_txt(file_path: str)`: Reads and extracts content/summary from a TXT file.
*   `read_pdf(file_path: str)`: Reads and extracts content/summary from a PDF file.

### `util_functions/sql_operations.py`

*   `list_tables(engine: Engine)`: Lists tables in the database.
*   `describe_table(engine: Engine, table_name: str)`: Describes the schema of a given table.
*   `run_sql_query(engine: Engine, query: str, limit: int)`: Executes a SQL query and returns results.

## Setup and Running

### Prerequisites

*   Python 3.9+
*   Poetry (recommended for dependency management)
*   PostgreSQL database (e.g., `chinook` database)
*   OpenAI API Key (or Azure OpenAI credentials)
*   Logfire Token (optional, for observability)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/Pydantic_Langgraph_SQL_and_File_Reader_Agents.git
    cd Pydantic_Langgraph_SQL_and_File_Reader_Agents
    ```
2.  **Install dependencies**:
    ```bash
    poetry install
    ```
3.  **Environment Variables**: Create a `.env` file in the root directory and add your credentials:
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

The `main.py` script contains examples of how to use the `MasterAgent`.

To run the examples:

```bash
poetry run python main.py
```

You can modify the `main` function in `main.py` to test different user requests.

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