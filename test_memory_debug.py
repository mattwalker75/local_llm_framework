#!/usr/bin/env python3
"""
Debug script to test memory tool calling integration.
"""

import json
import logging
from llf.config import Config
from llf.model_manager import ModelManager
from llf.prompt_config import PromptConfig
from llf.llm_runtime import LLMRuntime

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 80)
    print("MEMORY TOOL CALLING DEBUG TEST")
    print("=" * 80)

    # Initialize components
    print("\n1. Initializing components...")
    config = Config()
    model_manager = ModelManager(config)
    prompt_config = PromptConfig()
    runtime = LLMRuntime(config, model_manager, prompt_config)

    # Check if memory is enabled
    print("\n2. Checking memory status...")
    memory_manager = prompt_config.get_memory_manager()
    if memory_manager:
        print(f"   ✓ Memory manager initialized")
        print(f"   ✓ Enabled memories: {list(memory_manager.enabled_memories.keys())}")
    else:
        print(f"   ✗ Memory manager NOT initialized or no enabled memories")
        return

    # Check if tools are available
    print("\n3. Checking memory tools...")
    tools = prompt_config.get_memory_tools()
    if tools:
        print(f"   ✓ {len(tools)} memory tools available:")
        for tool in tools:
            print(f"      - {tool['function']['name']}")
    else:
        print(f"   ✗ No memory tools available")
        return

    # Build test message
    print("\n4. Building test message...")
    messages = prompt_config.build_messages("Remember that I prefer concise responses")
    print(f"   ✓ Built {len(messages)} messages")
    print(f"   ✓ System prompt includes memory instructions: {'Long-Term Memory' in messages[0]['content']}")
    print(f"\n   System prompt preview:")
    print(f"   {messages[0]['content'][:500]}...")

    # Check if server is running
    print("\n5. Checking LLM server status...")
    try:
        runtime._ensure_server_ready()
        print("   ✓ LLM server is running")
    except Exception as e:
        print(f"   ✗ LLM server not running: {e}")
        print("\n   Start the server with: llf start")
        return

    # Test tool calling
    print("\n6. Testing tool calling with LLM...")
    print("   Sending message: 'Remember that I prefer concise responses'")
    print("   (This should trigger the add_memory tool)")
    print("\n" + "=" * 80)

    try:
        # Make the request
        test_messages = [{"role": "user", "content": "Remember that I prefer concise responses"}]
        response = runtime.chat(test_messages, stream=False)

        print("\n" + "=" * 80)
        print("RESPONSE:")
        print("=" * 80)
        print(response)
        print("=" * 80)

        # Check if memory was actually added
        print("\n7. Checking if memory was stored...")
        from llf.memory_tools import execute_memory_tool

        search_result = execute_memory_tool(
            "search_memories",
            {"query": "concise"},
            memory_manager
        )

        if search_result["success"] and search_result["count"] > 0:
            print(f"   ✓ SUCCESS! Found {search_result['count']} memory entries:")
            for memory in search_result["memories"]:
                print(f"      - ID: {memory['id']}")
                print(f"        Content: {memory['content']}")
                print(f"        Type: {memory['type']}")
                print(f"        Importance: {memory['importance']}")
        else:
            print(f"   ✗ FAILED: No memory entries found")
            print(f"   This means the LLM did not use the add_memory tool")
            print(f"\n   Possible reasons:")
            print(f"   1. The model doesn't support function calling")
            print(f"   2. The model didn't recognize it should use the tool")
            print(f"   3. llama-server doesn't support function calling with this model")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
