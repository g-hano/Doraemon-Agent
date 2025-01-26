from pydantic import BaseModel, Field, PrivateAttr
from typing import Type, Dict
from langchain_core.tools import BaseTool
import os

class ToolCreationSchema(BaseModel):
    file_name: str = Field(
        description="Filename to save the new tool (e.g., 'finance_tools.py')"
    )
    tool_name: str = Field(
        description="Base name for the tool and schema (e.g., 'Multiply')"
    )
    parameters: Dict[str, str] = Field(
        description="Dictionary of parameter names to types (e.g., {'num1': 'int', 'num2': 'int'})"
    )
    purpose: str = Field(
        description="Clear description of what the tool does and its formula/algorithm"
    )

class ToolCreationTool(BaseTool):
    name: str = "ToolCreationTool"
    description: str = """
Use this tool to create new Python tools. Provide:
- file_name: Python filename to save (e.g., 'my_tools.py')
- tool_name: Base name for the tool (e.g., 'CustomTool')
- parameters: Dictionary of {param_name: type_string}
- purpose: Description AND implementation code for the tool.

Example:
{
    "file_name": "text_tools.py",
    "tool_name": "TextProcessor",
    "parameters": {"text": "str", "repeat_count": "int"},
    "purpose": "Repeats the input text a specified number of times. Implementation: return text * repeat_count"
}
"""
    args_schema: Type[BaseModel] = ToolCreationSchema
    verbose: bool = True
    _manager = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        self._manager = None

    def set_manager(self, manager: any):
        """Set the tool manager after initialization"""
        self._manager = manager

    def _run(self, file_name: str, tool_name: str, parameters: Dict[str, str], purpose: str) -> str:
        if not self._manager:
            return "Tool manager not set. Cannot create new tools."

        # Extract implementation code from purpose if it contains "Implementation:"
        implementation_code = ""
        imports = []
        description = purpose
        if "Implementation:" in purpose:
            parts = purpose.split("Implementation:", 1)
            description = parts[0].strip()
            implementation_code = parts[1].strip()

            # Extract imports if specified
            if "IMPORTS:" in implementation_code:
                import_part, code_part = implementation_code.split("IMPORTS:", 1)
                imports = [line.strip() for line in import_part.split(';') if line.strip()]
                implementation_code = code_part.strip()

        full_code = ""
        if imports:
            full_code += "\n".join(imports) + "\n\n"  

        # Generate Schema Class
        schema_code = f"""from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class {tool_name}Schema(BaseModel):\n"""
        for param, ptype in parameters.items():
            ptype = ptype.lower()
            if ptype == "string":
                ptype = "str"
            elif ptype == "integer":
                ptype = "int"
            elif ptype == "dictionary":
                ptype = "dict"
            schema_code += f"    {param}: {ptype} = Field(description='{ptype} value for {param}')\n"

        # Generate Tool Class
        tool_code = f"""
from langchain_core.tools import BaseTool
from typing import Type

class {tool_name}Tool(BaseTool):
    name: str = "{tool_name}"
    description: str = '''{description}'''
    args_schema: Type[BaseModel] = {tool_name}Schema
    verbose: bool = True

    def _run(self, {', '.join(f'{p}: {t}' for p, t in parameters.items())}) -> any:
        {implementation_code or '# Add implementation here'}
"""

        full_code += schema_code + tool_code
        
        # Write and validate code
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            file_name = os.path.join(script_dir, file_name)
            with open(file_name, "w") as f:
                f.write(full_code)
            
            # Load the newly created tool
            if self._manager.load_tool(file_name, tool_name):
                self._manager.refresh_agent()
                return f"Successfully created and loaded {tool_name}Tool from {file_name}"
            else:
                return f"Tool was created but couldn't be loaded. Check the implementation."
            
        except Exception as e:
            return f"Tool creation failed: {str(e)}"