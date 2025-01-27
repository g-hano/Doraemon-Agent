import argparse
from importlib import import_module
from pprint import pprint
from tool_manager import ToolManager

# Define the LLM mapping
LLM_MAPPING = {
    "ollama": ("langchain_ollama", "ChatOllama"),
    "openai": ("langchain_openai", "ChatOpenAI"),
    "anthropic": ("langchain_anthropic", "ChatAnthropic"),
}

def get_llm(llm_type, model_name):
    """
    Dynamically import and instantiate the specified LLM.
    """
    if llm_type not in LLM_MAPPING:
        raise ValueError(f"Unsupported LLM type: {llm_type}. Choose from {list(LLM_MAPPING.keys())}")

    module_name, class_name = LLM_MAPPING[llm_type]
    module = import_module(module_name)
    llm_class = getattr(module, class_name)
    return llm_class(model=model_name)

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Run an LLM with a specified model.")
    parser.add_argument(
        "--llm-type",
        type=str,
        required=True,
        choices=["ollama", "openai", "anthropic"],
        help="Type of LLM to use (ollama, openai, anthropic).",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        required=True,
        help="Name of the model to use (e.g., 'qwen2.5:14b' for Ollama).",
    )
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="The query to pass to the LLM.",
    )
    args = parser.parse_args()

    # Get the LLM instance
    llm = get_llm(args.llm_type, args.model_name)

    # Initialize the ToolManager and invoke the query
    tool_manager = ToolManager(llm)
    response = tool_manager.invoke(args.query)

    # Print the response
    print()
    pprint(response["messages"][-1].content)

if __name__ == "__main__":
    main()