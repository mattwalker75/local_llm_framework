# Local LLM Framework (LLF)

A flexible Python framework designed to run Large Language Models (LLM's) locally using [Llama.ccp](https://github.com/ggml-org/llama.cpp.git), or connect to an external LLM, such as OpenAI (ChatGPT), Anthropic, etc.  It can work with any external API that supports the OpenAI API integration.

## Overview

The Local LLM Framework (LLM) provides maximum flexibility enabling all aspects of the tool to be modularaly based that can be dynamically enabled and disabled on the fly.  You have the ability to run LLM's fully offline locally to perform tasks or use the framework to seemlessly integrate and work with external popular LLM models, such as ChatGPT.  LLM fully supports any external LLM that supports that OpenAI API integration.  

## Key Features

The following are the main key features of the Local LLM Framework (LLM):

- Management
   - Command line based with its own set of commands and sub-command ( similar to docker )
   - Web based GUI interface
- User interface with LLM
   - Terminal based interaction
   - Command line interface 
      - Enables the ability to incorporate LLM logic in local shell scripts and automation
   - Web based GUI interface
- LLM support
   - Local LLM's from [Hugging Face](https://huggingface.co) 
      - Must be able to be converted to GGUF format
   - Downloadable LLM's that can be converted to GGUF format
   - External LLM's that support OpenAI API protocol
   - Public LLM's (such as ChatGPT) that support OpenAI API protocol
- Local LLM management
   - Host a single or multiple LLM's 
   - Locally running LLM's is placed behind an OpenAI API interface
      - You can perform OpenAI API development against locally running LLM's
   - Optionally allow users on your network to access your locally running LLM's
- LLM model management
   - Integrated download of LLM's from [Hugging Face](https://huggingface.co) 
- GUI interface
   - Web browser GUI interface support
   - Use the GUI interface locally or across a local network
   - All command line control available through the GUI interface
   - Optionally add GUI authentication for added security
   - Optionally restrict GUI access for local use
- LLM memory
   - Optionally enable local LLM memory for user interaction
   - Save custom data for the LLM to recall across multiple sessions
   - View and edit the LLM memory data
   - LLM memory is fully managed by the LLM itself and stored locally
- Module support
   - Supports text to speech funcationality
      - This enables the LLM to "talk" to you over the local speakers
   - Supports speech to text functionality
      - This enable the end user to "talk" to the LLM 
- Tool support
   - Enable the ability to allow the LLM to use tools
      - Enable the LLM to access the Internet for research
      - Enable the LLM to access files on your local computer
         - Enable white list support of what directories and files the LLM can access
      - Enable the LLM to run commands on your local computer
         - Enable while list support of what commands the LLM can execute

## Index 

The following is the index of data sources and how-to's to get your up and running

- [Setup and installation](QUICK_INSTALL.md)
- [ALWAYS USE THIS VIRTUAL ENVIROMENT!!!](docs/virtual_environment.md)
- [Major components](docs/Major_Components.md)
- [Directory Structure](docs/Directory_Structure.md)
- [Basic User Guide](docs/Basic_User_Guide.md)
- [Helpful Commands](docs/Helpful_Commands.md)
- [Tools Directory](docs/Tools.md)
- Differnet configuration files
   - [main configuration config.json](docs/Config_Files/config_json.md)
   - [LLM prompt configuration config_prompt.json](docs/Config_Files/config_prompt_json.md)
   - [Data Store registry data_store_registry.json](docs/Config_Files/data_store_registry_json.md)
   - [Memory registry memory_registry.json](docs/Config_Files/memory_registry_json.md)
   - [Module registry modules_registry.json](docs/Config_Files/modules_registry_json.md)
   - [Tool registry tools_registry.json](docs/Config_Files/tools_registry_json.md)
- How To documents
   - [Cool stuff to do with chat](docs/HOW_TOs/Fun_With_Chat.md)
   - [Use LLM as your personal documentation reference tool](docs/HOW_TOs/Setup_Datastore_RAG.md)
   - [Have LLM remember anything you want](docs/HOW_TOs/Setup_Memory.md)
   - [How to talk to the LLLM and have it talk back](docs/HOW_TOs/Setup_Talking.md)
   - [Use all these tools with ChatGTP](docs/HOW_TOs/Setup_External_LLM.md)
   - [Access the backend local LLM from another computer](docs/HOW_TOs/Setup_Network_Access_LLM.md)
   - [Access the GUI from another computer](docs/HOW_TOs/Setup_Network_Access_GUI.md)
   - [How to download and use other LLM's](docs/HOW_TOs/Setup_LLMs.md)
   - [Troubleshooting Notes](docs/HOW_TOs/Troubleshooting.md)
 
## System Requirements
We will review what computer hardware was used for the developement of the LLM framework..
-  **CPU**: Apple M2 Ulta 
-  **RAM**: 64G
-  **Python version**:  3.13.5


