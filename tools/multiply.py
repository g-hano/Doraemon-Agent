from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class MultiplySchema(BaseModel):
    num1: float = Field(description='float value for num1')
    num2: float = Field(description='float value for num2')

from langchain_core.tools import BaseTool
from typing import Type

class MultiplyTool(BaseTool):
    name: str = "Multiply"
    description: str = '''Multiplies two numbers together.'''
    args_schema: Type[BaseModel] = MultiplySchema
    verbose: bool = True

    def _run(self, num1: float, num2: float) -> any:
        return num1 * num2
