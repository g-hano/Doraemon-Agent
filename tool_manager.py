from typing import Dict
from langchain_core.tools import BaseTool
import importlib.util
import sys
from system_prompt import SYSTEM_PROMPT
from tools.tool_creation import ToolCreationTool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

class ToolManager:
    def __init__(self, llm, base_tools: dict | None={}):
        self.loaded_tools: Dict[str, BaseTool] = base_tools or {}
        self.llm = llm
        self.tool_creation_tool = ToolCreationTool()
        self.tool_creation_tool.set_manager(self) 
        self.agent = self._create_agent()
        self._current_attempt = 0
        self.new_tool_added = None  # Add this flag

    def _create_agent(self, tools=None) -> any:
        if tools is None:
            tools = [self.tool_creation_tool]
        print(f"\nCreating agent with {len(tools)} tools:")
        
        #system_content = SYSTEM_PROMPT.replace(
        #    "{tool_names}",
        #    ", ".join([t.name for t in tools])
        #)       
        tool_info = [f"{t.name} ({t.description})" for t in tools]

        system_content = SYSTEM_PROMPT.replace(
            "{tool_names}",
            ", ".join(tool_info)+"\n"
        ) 
        return create_react_agent(
            self.llm,
            tools,
            state_modifier=system_content,
        )

    def refresh_agent(self):
        """Recreate the agent with updated tools"""
        print("Refreshing")
        tools = [self.tool_creation_tool] + list(self.loaded_tools.values())
        #self.agent = None
        self.agent = self._create_agent(tools)

    def load_tool(self, file_name: str, tool_name: str) -> bool:
        try:
            module_name = file_name.replace(".py", "")
            spec = importlib.util.spec_from_file_location(module_name, file_name)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Get the tool class
            tool_class = getattr(module, f"{tool_name}Tool")
            tool_instance = tool_class()
            if not isinstance(tool_instance, BaseTool):
                raise ValueError("Created tool is not a BaseTool instance")
            if not hasattr(tool_instance, "_run"):
                raise ValueError("Tool missing _run method")
            
            self.loaded_tools[tool_name] = tool_instance
            self.refresh_agent()
            self.new_tool_added = True  # Add this flag
            return True
        except Exception as e:
            print(f"Tool loading error: {str(e)}")
            return False
    
    def list_tools(self):
        return ["ToolCreationTool"] + list(self.loaded_tools.keys())  

    def invoke(self, query: str, max_retries: int = 3):
        """Handle query execution with automatic retries after tool creation"""
        self._current_attempt = 0
        response = None
        
        while self._current_attempt < max_retries:
            self._current_attempt += 1
            print(f"\nAttempt {self._current_attempt}")
            
            # Create fresh messages dict each attempt
            messages = [HumanMessage(content=query)]
            
            # Execute with current agent configuration
            response = self.agent.invoke({"messages": messages})
            
            # Check if we need to retry
            if not self.new_tool_added:
                break
                
            # Reset flag for next attempt
            self.new_tool_added = False
            
        return response