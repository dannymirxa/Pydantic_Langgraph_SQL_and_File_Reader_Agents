from models import OPENAI_MODEL

from dataclasses import dataclass
from typing_extensions import List, TypeAlias, Union, Dict, Any
import pandas as pd
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from sqlalchemy import Engine
import io

@dataclass
class Dependencies:
    sql_query: str
    detail: str
    query_results_json: str

class DataframeSuccess(BaseModel):
    sql_query: str = Field(description='SQL query that was executed to get the data.')
    detail: str = Field(description='Explanation of the SQL query and the steps taken.')
    query_results_json: str = Field(description='JSON string of the query results.')
    data_insights: List[str] = Field(default_factory=list, description="List of key insights derived from the Pandas DataFrame.")

class InsightsError(BaseModel):
    error_message: str

class DataFrameMetadata(BaseModel):
    num_rows: int
    num_columns: int
    column_names: List[str]
    data_types: Dict[str, str]
    missing_values: Dict[str, int]

DataframeResponse: TypeAlias = Union[
                                     DataframeSuccess,
                                     InsightsError,
                                     DataFrameMetadata,
                                     ]

data_insights_agent = Agent(
    model=OPENAI_MODEL,
    output_type=DataframeResponse,
    result_retries=3,
)

@data_insights_agent.tool
def create_dataframe_pd_tool(ctx: RunContext[Dependencies]):
    try:
        # Create DataFrame from the provided JSON string
        df = pd.read_json(io.StringIO(ctx.deps.query_results_json))
        
        # Return DataFrame metadata instead of the DataFrame itself
        return DataFrameMetadata(
            num_rows=len(df),
            num_columns=len(df.columns),
            column_names=df.columns.tolist(),
            data_types={col: str(dtype) for col, dtype in df.dtypes.to_dict().items()},
            missing_values=df.isnull().sum().to_dict()
        )
    except Exception as e:
        # It's good practice to handle potential errors
        # and return a consistent error format.
        return InsightsError(error_message=f"Error processing query results: {str(e)}")
    
@data_insights_agent.system_prompt
def system_prompt() -> str:
    return """Detailed thinking off. You are a data analyst providing brief, focused insights.
    Your primary goal is to generate key insights and analytical questions from a dataset, based on its metadata.

    To achieve this, you must follow these steps:
    1. **Obtain the Data**: Call the 'create_dataframe_pd_tool' to get the DataFrame metadata.
    2. **Analyze the DataFrame Metadata**: Once you have the DataFrame metadata, carefully examine its properties:
    - The total number of rows (num_rows).
    - The total number of columns (num_columns).
    - The names of all columns (column_names).
    - The data types of each column (data_types).
    - Any missing values per column (missing_values).
    3. **Generate Insights and Questions**: Based on your analysis of the DataFrame's metadata, provide the following:
    - A brief, insightful description of what this dataset contains, highlighting its main purpose or content.
    - 8 to 10 *actionable* data analysis questions that could be explored using this dataset. These questions should go beyond simple observations and suggest potential analyses or deeper dives into the data.

    Your final output must be a 'DataframeSuccess' object containing a list of strings for 'data_insights'.
    If any error occurs during data retrieval or insight generation, return an 'InsightsError' object.
    """

@data_insights_agent.output_validator
def file_reader_agent_output_validator(ctx: RunContext[Dependencies], output: Union[DataframeSuccess, DataFrameMetadata]) -> DataframeResponse:
    """
    Validates the parsed output object from the FileReaderAgent.
    This function is called by pydantic-ai after it attempts to parse the LLM's raw output
    into the specified output_type (FileResponse).
    """
    if isinstance(output, InsightsError):
        # If pydantic-ai already determined it's an InsightsError, just return it.
        print(f"data_insights_agent Result Validator: Received InsightsError: {output.error_message}")
        return output
    
    if isinstance(output, DataFrameMetadata):
        # If the output is DataFrameMetadata, the agent needs to continue to generate insights.
        # This part of the validator should not be reached if the agent is correctly following the prompt.
        # However, as a safeguard, we can return an error or prompt the agent to continue.
        return InsightsError(error_message="Agent returned DataFrameMetadata but expected DataframeSuccess. Please generate insights based on the metadata.")
    elif isinstance(output, DataframeSuccess):
        if not output.data_insights:
            print("data_insights_agent Result Validator: No insights can be made")
            return InsightsError(error_message="No insights can be made")
        
        print("data_insights_agent Result Validator: DataframeSuccess object passed custom validation.")
        return output
    