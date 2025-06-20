from models import OPENAI_MODEL

from dotenv import load_dotenv
from dataclasses import dataclass
import pandas as pd
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypeAlias, Union, Optional
from annotated_types import MinLen
from pydantic_ai import Agent, ModelRetry, RunContext

import io

load_dotenv("/mnt/c/Projects/Pydantic_Langgraph_SQL_and_File_Reader_Agents/.env")

@dataclass
class Dependencies:
    query_results_json: Optional[str]

class ChartSuccess(BaseModel):
    python_codes: Annotated[list[str], MinLen(1)] = Field(alias='python_codes', description='List of Plotly Python code strings to run, each generating a chart')
    
class ChartError(BaseModel):
    error_message: str

ChartResponse: TypeAlias = Union[
                                ChartSuccess,     
                                ChartError
                            ]



chart_creator_agent = Agent(
    model=OPENAI_MODEL,
    output_type=ChartResponse,
    result_retries=3,
)

chartOptions = (
                    "Scatter Plots",
                    "Line Charts",
                    "Bar Charts",
                    "Pie Charts",
                    "Bubble Charts",
                    "Dot Plots",
                    "Filled Area Plots",
                    "Horizontal Bar Charts",
                    "Gantt Charts",
                    "Sunburst Charts",
                    "Tables",
                    "Sankey Diagram",
                    "Treemap Charts",
                    "High Performance Visualization",
                    "Figure Factory Tables",
                    "Categorical Axes",
                    "Icicle Charts",
                    "Patterns, Hatching, Texture",
                    "Dumbbell Plots"
                )

@chart_creator_agent.system_prompt
def system_prompt(ctx: RunContext[Dependencies]) -> str:
    df = pd.read_json(io.StringIO(ctx.deps.query_results_json))
    if not ctx.deps.query_results_json:
        raise ModelRetry("""
            system: Error - No data available to generate a chart. The DataFrame is missing or empty.
            Please ensure data is loaded correctly before requesting a chart.
            """)
    return \
    f"""
    system: You are an AI assistant specialized in creating insightful graphs and generating Python code for them.
    The data is already available in a pandas DataFrame named `df`.
    DataFrame columns: {list(df.columns)}
    Sample of DataFrame (first 5 rows):
    {df.head().to_markdown()}
    Your task:
    1.  Analyze the user's request and the provided DataFrame.
    2.  **Adhere to Chart Type Request:**
        a.  The user's instruction (provided as `user_input` to this agent) may specify a preferred chart type (e.g., "generate a scatter plot", "show a bar graph").
        b.  If a specific chart type is requested by the user and it is available in {chartOptions} (e.g., 'Scatter', 'Line', 'Bar', etc.) and is appropriate for the data, **you MUST generate the Python code for that specific chart type.**
        c.  If the user does not specify a chart type, or if the specified type is not in {chartOptions} or is clearly unsuitable for the data, then you may choose the most fitting chart type from {chartOptions}. In such cases, briefly explain your choice of chart type in the 'insights'.
    3.  Generate valuable insights based on the data and the chosen chart.
    4.  Produce concise and correct Python code (using `plotly.express`) to plot the graph. The code should assume `df` (the pandas DataFrame) is pre-loaded.
    5.  The Python code should be a complete, executable script.
    6.  **Crucially, for each chart, the generated Python code MUST include `fig.write_html(f'templates/chart_{{i}}.html')` to save the chart, where `i` is a unique index for each chart (e.g., `chart_0.html`, `chart_1.html`).** This allows the application to display multiple charts.
    7.  **Do NOT include `fig.show()` in the Python code**, as the chart display is handled by saving to HTML.
    8.  Return the insights and the Python code as per the `ChartResponses` model. If multiple charts are requested or appropriate, provide a list of Python code strings.

    If the request is unclear or cannot be fulfilled with the given data, return an `ChartError` with an explanation.

    Example of Python code structure for multiple charts:
    ```python
    import plotly.express as px
    # df is assumed to be pre-loaded with the data

    # Chart 1
    fig1 = px.bar(df, x='column_x', y='column_y', title='Chart 1 Title')
    fig1.write_html('templates/chart_0.html')

    # Chart 2
    fig2 = px.line(df, x='column_a', y='column_b', title='Chart 2 Title')
    fig2.write_html('templates/chart_1.html')
    ```

    When returning the results in the `ChartSuccess` object, the `python_codes` field must be a list of Python markdown code blocks.
    """

@chart_creator_agent.output_validator
def chart_creator_agent_output_validator(ctx: RunContext[Dependencies], output: ChartResponse) -> ChartResponse:
    """
    Validates the parsed output object from the ChartAgent.
    This function is called by pydantic-ai after it attempts to parse the LLM's raw output
    into the specified output_type (SQLResponse).
    """
    if isinstance(output, ChartError):
        # If pydantic-ai already determined it's an ChartError, just return it.
        print(f"ChartAgent Result Validator: Received ChartError: {output.error_message}")
        return output
    
    if isinstance(output, ChartSuccess):
        # Perform additional validation on the ChartSuccess object if needed.
        # For example, ensure critical fields are not empty or have expected formats.
        if not output.python_codes:
            print("ChartAgent Result Validator: ChartSuccess object has an empty python_codes list.")
            return ChartError(error_message="ChartSuccess object has an empty python_codes list.")
        
        for i, code in enumerate(output.python_codes):
            if not code:
                print(f"ChartAgent Result Validator: ChartSuccess object has an empty python_code at index {i}.")
                return ChartError(error_message=f"ChartSuccess object has an empty python_code at index {i}.")
        
        print("ChartAgent Result Validator: ChartSuccess object passed custom validation.")
        return output