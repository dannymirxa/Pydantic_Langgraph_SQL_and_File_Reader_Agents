from pydantic import BaseModel, Field
from typing import Annotated, List, Dict, Any, Optional, Union
from annotated_types import MinLen
from openai import AsyncAzureOpenAI, AzureOpenAI
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.providers.openai import OpenAIProvider

from dotenv import load_dotenv
import os

load_dotenv('.env')

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")

# GEMINI_MODEL = GeminiModel('gemini-2.0-flash', provider=GoogleGLAProvider(api_key=GEMINI_API_KEY))

async_client = AsyncAzureOpenAI(
    azure_endpoint = "https://llmcoechangemateopenai2.openai.azure.com/",
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-10-21",
    azure_deployment='gpt-4o'
)

OPENAI_MODEL = OpenAIModel(
    'gpt-4o',
    provider=OpenAIProvider(openai_client=async_client),
)

class Request(BaseModel):
    query: Annotated[str, MinLen(1)]

# class ChartResponses(BaseModel):
#     insights: Annotated[str, MinLen(1), Field(alias='insights', description="insights from the dataset and graph")]
#     python_code: Annotated[str, MinLen(1), Field(alias='python_code',description='Python code to plot the graph, as markdown')]

class ChartSuggestion(BaseModel):
   type: str = Field(description="Type of chart (e.g., 'bar', 'line', 'pie', 'scatter')")
   x_axis: Optional[str] = Field(description="Column name for the X-axis")
   y_axis: Optional[str] = Field(description="Column name for the Y-axis")
   series: Optional[List[str]] = Field(description="Column names for series/groups")
   title: Optional[str] = Field(description="Suggested chart title")
