
# Major Components of the LLF Platform

## Backend LLM Server
NOTE:  This is ONLY needed if you are going to run LLM's locally
- Run local LLM's behind an [OpenAI](https://platform.openai.com/docs/quickstart) interface
- Runs on [Llama.cpp](https://github.com/ggml-org/llama.cpp)

---

## Frontend Client
- Framework management tools
   - Primary command used `bin/llf`
- CLI and Interactive terminal interface to LLM
- LLM Server management
   - Only applicable if running Backend LLM Server
- LLM Model download and management
   - Only applicable if running Backend LLM Server
   - Your Memory size highly dictates the size of LLM that you can run
- GUI interface to LLM and management tools
- Data Store Management
   - These are local RAG Vector Stores
      - Fully customize and manage
   - Store text data for the LLM to query
      - Supports PDF, DOC(X), TXT, MD, Web Site text
   - Have the AI do the lookups in your documentation for you 
- Memory Management
   - Setup and define longterm memory for the AI to use.
   - The AI fully manages the memory, you just tell it what it should remember
   - You can look at and modify the AI memory at any time
- Module Management
   - Control different level of interactions between you and the AI
   - Here are the options you can dynamically enable
      - Use the default engagement with the AI during chat, which is text based
      - Enable the AI to talk to you over the speakers of your computer
      - Enable yourself to talk to the AI via a microphone
- Tool Management
   - Enable the AI to perform tasks on your behalf
      - Have AI search the Internet and get data
      - Allow AI to work with files on your computer via white list access controls
         - White list access controls means you use a configuration file to tell the AI exactly what files and directories it can access
      - Allow AI to run commands on your computer via white list access controls
         - White list access controls means you use a configuration file to tell the AI exactly what commands it can run on your behalf

NOTE:  All the management tools can be dynamically changed as needed




