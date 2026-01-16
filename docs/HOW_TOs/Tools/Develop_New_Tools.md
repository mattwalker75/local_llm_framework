
# Creating your own custom tools

> You can create your own custom tools for the LLM to use to perform operations to interact with the environment.  
---

## Create a new tool

You can run the following interactive command to create the framework for your new tool
```bash
llf dev create-tool
```

This will provide an interactive system where you determine and fill out the following information.

### Select tool Integration

How will the tool be used by the LLM:
- Is it a tool that the LLM will call directly as a function during a conversation
- Is it a process that gets executed to modify the LLM's output before sending it to the user
- Is it a process that gets executed to modify the user input data before it gets sent to the LLM

### Name and Describe the tool

Come up with a name to call the tool that makes sense.

Provide a description of what the tool is for and how to use it

### Categorize the tool

Determine which catagory this tool should fall under.  This is strictly for organization and serves no real functional purpose.

### Determine if you want to enable parameters to be passed to your tool or not

Map our the parameters that you want to pass to the tool to be used for execution along with the data type of the parameter.

The following data types are supported for parameters
   - string
   - integer
   - number
   - boolean
   - array 
   - object

Provide a description of the parameter(s) and determine which ones are required and which ones are optional.

### Select the code template to use

Select the code template to use for the the tool.  The following are supported
- Calling external HTTP/REST API's
- Fetching and Parsing web pages
- Reading/Writting local files
- Executing shell commands with security checks
- Query databases
- Empty template with "TO DO" comments for custom implementation

### It will provide next steps

After generating the initial code, you will get  the following type of output:
```
✓ Successfully created tool scaffold for 'hello_world_test_tool' in
/directory/to/local_llm_framework/tools/hello_world_test_tool

Next Steps:

1. Review generated files in: /directory/to/local_llm_framework/tools/hello_world_test_tool
2. Implement the execute() function in __init__.py
3. Update README.md with actual usage examples
4. Write tests in tests/test_hello_world_test_tool.py
5. Run tests: pytest tests/test_hello_world_test_tool.py
6. When ready, import to registry: llf tool import hello_world_test_tool
7. Enable the tool: llf tool enable hello_world_test_tool
```

---

## What is in your custom tool directory

The following files get generated and are within your tools directory

### __init__.py
The main implementation file containing the `execute()` function that performs the actual tool logic and the `TOOL_DEFINITION` constant that defines the tool's schema for the LLM.  The content of hte `TOOL_DEFINITION` should be exactly the same as what is in the `tool_definition.json` file

### execute.py
A compatibility wrapper that simply re-exports the execute function from `__init__.py` to support different import patterns.  When the LLM needs to execute your tool, it looks for a file called `execute.py` in the tool directory and calls the `execute` function from it.

### tool_definition.json
JSON schema file that describes the tool's function signature (name, description, parameters) in the format expected by LLMs for function calling.  This tells the LLM:
- What your tool does
- What parameters it needs to execute
- The name of the tool that the LLM will invoke

Below is an example `tool_definition.json` file

```json
{
  "type": "function",
  "function": {
    "name": "hello_world_test_tool",  // ← Function name LLM will call
    "description": "...",             // ← WHEN to use this tool
    "parameters": {                   // ← HOW to call it
      "type": "object",
      "properties": {
        "name": {                     // ← Parameter name
          "type": "string",           // ← Parameter type
          "description": "..."        // ← What this parameter is for
        }
      },
      "required": ["name"]            // ← Which parameters are mandatory
    }
  }
}
```

### config.json
Registry metadata file containing tool configuration like enabled status, category, dependencies, and other administrative settings used by the LLF ToolsManager.  This is the data that gets populated in the tools `tools_registry.json` Registry file when you perform a `llf tool import` command.

---

## Add some code to your tool 

All your code will go into the following file
- __init__.py

NOTE:  The `TOOL_DEFINITION` within the `__init__.py` should be identical to the content in the `tool_definition.json` file.  The `tool_definition.json` file is used by the `llf` CLI tool, such as when importing and listing information about the tool.  The `TOOL_DEFINITION` is used by the LLM at runtime and during tool execution.

The first part of the file will import sime required libraries and initialize logging.
```
from llf.logging_config import get_logger
from typing import Dict, Any

logger = get_logger(__name__)
```

The next part is your `TOOL_DEFINITION` that tells the LLM how to use your tool during LLM runtime and tool execution.
```json
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "hello_world_test_tool",
        "description": "This should provide a useful description that the LLM can use to determine how to use this tool",
        "parameters": {
                "type": "object",
                "properties": {
                        "name": {
                                "type": "string",
                                "description": "This should provide a useful description that the LLM can use to determine what type of data to use for this parameter"
                        }
                },
                "required": [
                        "name"
                ]
        }
    }
}
```

The following is the main code for your LLM tool.  Typically when using the `llf dev create-tool` command, this will be the only section of code that you will need to modify.  Think of the `execute()` function for LLM tooling like a traditional coding `main` statement in that your could execution will always start in `execute()` and you should always have it end in `execute()`.  As you can see, this is a simple `hello world` type of tool.
```
def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        name = arguments.get('name', 'NULL')
        greeting = f"Hello, {name}!  This is your test tool response!!!"

        logger.info(f"Generated greeting for: {name}")

        return {
            "success": True,
            "data": greeting
        }

    except Exception as e:
        logger.error(f"Tool had an error: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

The following line defines that the ONLY thing that should be accessible by outside processes, such as the LLM, is the `TOOL_DEFINITION` and the `execute` function.
```
__all__ = ['TOOL_DEFINITION', 'execute']
```

---

## How to execute your tool

Note:  The example code shows how you can simulate how the LLM would execute your tool to help ensure it returns the correct data to the LLM for analysis.

The following shows some example code of how to execute the tool from the current directory as the tool.
```
#!/usr/bin/env python3

from __init__ import execute

# Test 1: With a name parameter
print("\nTest 1: Calling with name='Matt'")
result1 = execute({"name": "Matt"})
print(f"Result: {result1}")
```

The following shows some example code of how to execute the tool from the `tools` directory.
```
#!/usr/bin/env python3

from hello_world_test_tool.__init__ import execute

# Test 1: With a name parameter
print("\nTest 1: Calling with name='Matt'")
result1 = execute({"name": "Matt"})
print(f"Result: {result1}")
```



