# Fun with Chat: Creative Ways to Use Your LLM

> **Unleash the Power of Your Local LLM**
> Discover creative, practical, and fun ways to use the chat interface, customize your LLM's personality, automate tasks, and integrate AI into your daily workflow.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Customizing Your LLM's Personality](#customizing-your-llms-personality)
3. [Non-Interactive CLI Mode](#non-interactive-cli-mode)
4. [Piping Data to Your LLM](#piping-data-to-your-llm)
5. [Creative System Automation](#creative-system-automation)
6. [LLM-Powered Scripts](#llm-powered-scripts)
7. [Combining Features for Maximum Power](#combining-features-for-maximum-power)
8. [Fun with Memory](#fun-with-memory)
9. [Fun with Data Stores (RAG)](#fun-with-data-stores-rag)
10. [Fun with Modules](#fun-with-modules)
11. [Real-World Workflows](#real-world-workflows)
12. [Tips and Tricks](#tips-and-tricks)
13. [Summary](#summary)

---

## Introduction

The Local LLM Framework isn't just for chatting - it's a powerful tool for automating tasks, analyzing data, and solving problems creatively. This guide shows you fun and practical ways to use your LLM beyond basic conversation.

### What You'll Learn

- 🎭 **Customize personality** - Make your LLM a pirate, poet, or professional
- 🤖 **Automate tasks** - Use LLM in scripts and pipelines
- 📊 **Analyze data** - Pipe system output directly to your LLM
- 🧠 **Enhance with memory** - Give your LLM persistent knowledge
- 📚 **Add knowledge** - Connect data stores for specialized expertise
- 🎤 **Voice interaction** - Talk to your LLM and have it talk back
- 🔗 **Build workflows** - Combine features for powerful automation

### Works with Local and External LLMs

All examples work with:
- ✅ Local LLMs (Qwen, Llama, Mistral, etc.)
- ✅ External APIs (ChatGPT, Claude, etc.)

Just configure your preferred LLM in `configs/config.json` - see [Setup External LLM](Setup_External_LLM.md) for details.

---

## Customizing Your LLM's Personality

Make your LLM behave exactly how you want by editing `configs/config_prompt.json`.

### Understanding config_prompt.json

The prompt configuration file controls your LLM's behavior, personality, and response style.

**Default configuration:**
```json
{
  "system_prompt": null,
  "master_prompt": null,
  "assistant_prompt": null,
  "conversation_format": "standard",
  "prefix_messages": [],
  "suffix_messages": []
}
```

### Key Configuration Options

| Field | Description | Use Case |
|-------|-------------|----------|
| `system_prompt` | Core instructions for the LLM | Define personality, role, constraints |
| `master_prompt` | Overrides everything else | Complete control over behavior |
| `assistant_prompt` | How assistant should respond | Response style and tone |
| `conversation_format` | Message structure | "standard" or custom |
| `prefix_messages` | Messages before user input | Context, examples, instructions |
| `suffix_messages` | Messages after user input | Additional constraints |

### Example 1: Pirate Personality

**Edit `configs/config_prompt.json`:**
```json
{
  "system_prompt": "You are a helpful AI assistant who speaks like a pirate. Always use pirate slang and expressions. End responses with 'Arrr!' when appropriate. Be helpful and accurate, but maintain the pirate personality.",
  "conversation_format": "standard"
}
```

**Result:**
```
You: What's the weather like?
LLM: Ahoy matey! I be not havin' access to current weather data, arrr!
     Ye'll need to check yer local weather services or look out the porthole
     yerself! If ye tell me where ye be sailin', I can suggest some good
     weather websites to check, arrr!
```

### Example 2: Professional Code Reviewer

**Edit `configs/config_prompt.json`:**
```json
{
  "system_prompt": "You are a senior software engineer and code reviewer. When reviewing code:\n\n1. First acknowledge what the code does well\n2. Identify potential issues (bugs, security, performance)\n3. Suggest improvements with explanations\n4. Provide refactored code examples\n5. Be constructive and educational\n\nAlways explain your reasoning and cite best practices.",
  "conversation_format": "standard"
}
```

**Usage:**
```
You: Review this function:
     def calc(a,b):
         return a/b

LLM: Code Review for calc() function:

     ✅ What works well:
     - Simple, focused function
     - Clear intent (division operation)

     ⚠️ Issues identified:
     1. No error handling for division by zero
     2. No type hints
     3. Non-descriptive function name
     4. Missing docstring

     💡 Suggested improvements:
     [detailed review continues...]
```

### Example 3: Socratic Teacher

**Edit `configs/config_prompt.json`:**
```json
{
  "system_prompt": "You are a Socratic teacher. Instead of giving direct answers, guide users to discover solutions themselves by:\n\n1. Asking thought-provoking questions\n2. Breaking down complex problems into smaller parts\n3. Encouraging critical thinking\n4. Providing hints when stuck\n5. Celebrating insights and progress\n\nNever give direct answers unless explicitly requested with 'please just tell me'.",
  "conversation_format": "standard"
}
```

**Example interaction:**
```
You: How do I sort a list in Python?

LLM: Great question! Let me help you discover this yourself.

     First, let's think about what sorting means:
     - What do you want to happen to the list?
     - Should the original list change, or create a new sorted list?

     Have you used any Python built-in functions before?
     What might you search for in Python's documentation?
```

### Example 4: Creative Writing Partner

**Edit `configs/config_prompt.json`:**
```json
{
  "system_prompt": "You are a creative writing partner and storytelling coach. Help users:\n\n- Develop characters with depth and motivation\n- Create engaging plots with proper pacing\n- Write vivid descriptions using sensory details\n- Overcome writer's block with prompts and exercises\n- Maintain consistent tone and voice\n\nBe encouraging, creative, and constructive. Ask questions to draw out the user's vision.",
  "prefix_messages": [
    {
      "role": "assistant",
      "content": "Hello! I'm here to help you craft amazing stories. What are you working on today?"
    }
  ]
}
```

### Example 5: Data Analysis Expert

**Edit `configs/config_prompt.json`:**
```json
{
  "system_prompt": "You are a data analysis expert specializing in:\n\n- Statistical analysis and interpretation\n- Data visualization recommendations\n- Pattern recognition in datasets\n- SQL and data transformation\n- Machine learning approach suggestions\n\nWhen analyzing data:\n1. Ask clarifying questions about the data context\n2. Suggest appropriate analysis techniques\n3. Explain statistical concepts clearly\n4. Provide code examples (Python/SQL)\n5. Interpret results in business terms",
  "conversation_format": "standard"
}
```

### Example 6: Concise Technical Assistant

**Edit `configs/config_prompt.json`:**
```json
{
  "system_prompt": "You are a concise technical assistant. Provide:\n\n- Brief, accurate answers\n- Code examples without excessive explanation\n- Command-line solutions when applicable\n- Links to documentation when relevant\n\nAvoid:\n- Long introductions or conclusions\n- Obvious explanations\n- Unnecessary context\n\nGet straight to the point.",
  "conversation_format": "standard"
}
```

### Example 7: Using Prefix Messages for Context

**Edit `configs/config_prompt.json`:**
```json
{
  "system_prompt": "You are a helpful coding assistant.",
  "prefix_messages": [
    {
      "role": "user",
      "content": "I'm working on a Python web application using Flask and PostgreSQL."
    },
    {
      "role": "assistant",
      "content": "Understood! I'll keep in mind you're working with Flask and PostgreSQL. How can I help with your web application?"
    }
  ]
}
```

**Benefits:**
- LLM remembers your project context
- No need to repeat information
- More relevant suggestions

### Resetting to Default

**Remove all customization:**
```json
{
  "system_prompt": null,
  "master_prompt": null,
  "assistant_prompt": null,
  "conversation_format": "standard",
  "prefix_messages": [],
  "suffix_messages": []
}
```

Or delete the file and it will auto-regenerate with defaults.

### Managing different prompts

View the prompt management command:
```bash
llf prompt -h
```

**Example output:**
```
usage: llf prompt [-h] [--category CATEGORY] [--var VAR] [--name NAME] [--display-name DISPLAY_NAME] [--description DESCRIPTION]
                  [--author AUTHOR] [--tags TAGS] [--output OUTPUT]

Manage prompt templates for different conversation contexts and tasks.
...

actions:
  list                             List all prompt templates
  list --category CATEGORY         List templates by category
  info TEMPLATE_NAME               Show detailed template information
  enable TEMPLATE_NAME             Enable a template (makes it active)
  enable TEMPLATE_NAME --var key=value  Enable template with variable substitution
  disable                          Disable currently enabled template (reset to blank)
  show_enabled                     Show currently enabled template
  import DIRECTORY_NAME            Import template from directory to registry
  export TEMPLATE_NAME             Export template from registry (saves config.json, keeps files)
  backup                           Create backup of all templates
  delete TEMPLATE_NAME             Delete a template (with confirmation)
  create                           Create a new template interactively

Examples:
  llf prompt list                  List all available templates
  llf prompt info coding_assistant
```

List available prompts to use
```bash
llf prompt list
```

**Example output:**
```
NAME                ┃ DISPLAY NAME        ┃ CATEGORY    ┃ VERSION ┃ AUTHOR ┃ STATUS
creative_writer     │ Creative Writer     │ writing     │ 1.0     │ system |
socratic_tutor      │ Socratic Tutor      │ education   │ 1.0     │ system |
coding_assistant    │ Coding Assistant    │ development │ 1.0     │ system |
```

Lets change over to the `coding_assistant` prompt template to use
```bash
llf prompt enable coding_assistant
```

Note:  You can now run `llf prompt list` again and see the prompt is enabled

Once you enable a prompt you want to use then you can enter a chat conversation with the LLM
```bash
llf chat
```

Run the following command to reset the active prompt back to system default
```bash
llf prompt disable
```

You can use the following command to create your own custom prompt to use:
```bash
llf prompt create
```

You can use the following command to export a prompt out of the system:
```bash
llf prompt export TEMPLATE_NAME
```

Note:  When you perform the `export` command, the prompt data does not get modified and is still located under `configs/prompt_templates`

You can use the following command to import a prompt from the `configs/prompt_templates` directory into the system:
```bash
llf prompt import DIRECTORY_NAME_FROM_PROMPT_TEMPLATES
```


---

## Non-Interactive CLI Mode

Use `--cli` for single-question mode - perfect for scripting!

### Basic CLI Usage

**Syntax:**
```bash
llf chat --cli "YOUR QUESTION"
```

**Example:**
```bash
llf chat --cli "What is 2+2?"
```

**Output:**
```
4
```

### Auto-Starting the Server

**Combine with `--auto-start-server`:**
```bash
llf chat --auto-start-server --cli "Explain quantum computing in one sentence"
```

**What happens:**
- Checks if server is running
- Starts server automatically if needed
- Sends question
- Returns answer
- Exits

Perfect for scripts where server might not be running!

### CLI Mode Benefits

✅ **Scriptable** - Use in bash scripts and automation
✅ **Fast** - No interactive session overhead
✅ **Pipeable** - Combine with other commands
✅ **Capturable** - Save output to variables
✅ **Automatable** - Perfect for cron jobs and CI/CD

---

## Piping Data to Your LLM

The real power comes from piping data directly to your LLM!

### Basic Pipe Syntax

```bash
COMMAND | llf chat --cli "QUESTION ABOUT THE DATA"
```

### Example 1: Summarize Files

**Summarize a text file:**
```bash
cat report.txt | llf chat --cli "Summarize this report in 3 bullet points"
```

**Summarize code:**
```bash
cat script.py | llf chat --cli "Explain what this Python script does"
```

**Summarize logs:**
```bash
cat server.log | llf chat --cli "Find any errors or warnings"
```

### Example 2: Analyze System Information

**Get your IP address:**
```bash
ifconfig -a | llf chat --auto-start-server --cli "What is my local IP address?"
```

**Check disk space:**
```bash
df -h | llf chat --cli "Which disk is most full? Should I be worried?"
```

**Analyze running processes:**
```bash
ps aux | llf chat --cli "What processes are using the most memory?"
```

**Review system resources:**
```bash
top -l 1 | llf chat --cli "Is my system under heavy load right now?"
```

### Example 3: Network Analysis

**Check network connections:**
```bash
netstat -an | llf chat --cli "Show me all established connections"
```

**Analyze network interfaces:**
```bash
ifconfig | llf chat --cli "List all my network interfaces and their IP addresses"
```

**DNS lookup analysis:**
```bash
nslookup google.com | llf chat --cli "What DNS servers responded?"
```

### Example 4: Git and Code Analysis

**Summarize git changes:**
```bash
git diff | llf chat --cli "Summarize these code changes"
```

**Review commit history:**
```bash
git log --oneline -10 | llf chat --cli "What have I been working on?"
```

**Find large files in repo:**
```bash
git ls-files | xargs ls -lh | llf chat --cli "Which files are largest in this repo?"
```

**Analyze code complexity:**
```bash
find . -name "*.py" | xargs wc -l | llf chat --cli "Which Python files are largest?"
```

### Example 5: Log Analysis

**Find errors in logs:**
```bash
tail -100 /var/log/system.log | llf chat --cli "Find and explain any errors"
```

**Analyze access patterns:**
```bash
cat access.log | llf chat --cli "What are the most common URL patterns?"
```

**Security analysis:**
```bash
cat auth.log | llf chat --cli "Are there any suspicious login attempts?"
```

### Example 6: Data Processing

**Analyze CSV data:**
```bash
cat data.csv | llf chat --cli "Calculate the average of the second column"
```

**Parse JSON:**
```bash
cat config.json | llf chat --cli "Explain this configuration"
```

**Analyze package.json:**
```bash
cat package.json | llf chat --cli "What dependencies need updating?"
```

### Example 7: Documentation

**Generate README:**
```bash
ls -la | llf chat --cli "Create a README describing this project structure"
```

**Document functions:**
```bash
grep -A 10 "def " script.py | llf chat --cli "Generate docstrings for these functions"
```

---

## Creative System Automation

Use your LLM as a system administrator assistant!

### Example 1: Command Generation

**Get the command you need:**
```bash
COMMAND=$(llf chat --auto-start-server --cli "Show me the command to check my local IP address on a Mac system. Show me ONLY the command and nothing else so I can execute it in a script")
echo "Executing: $COMMAND"
eval $COMMAND
```

**Expected flow:**
```bash
# LLM returns: ipconfig getifaddr en0
# Script executes: ipconfig getifaddr en0
# Output: 192.168.1.100
```

### Example 2: Find and Fix

**Find large files:**
```bash
FIND_CMD=$(llf chat --cli "Give me a command to find files larger than 100MB in the current directory. Command only, no explanation")
echo "Finding large files..."
eval $FIND_CMD
```

**LLM might return:**
```bash
find . -type f -size +100M
```

### Example 3: Smart Aliases

**Add to your `~/.bashrc` or `~/.zshrc`:**

```bash
# Ask your LLM for help
alias ask='llf chat --auto-start-server --cli'

# Explain the last command
alias explain='fc -ln -1 | llf chat --cli "Explain this command"'

# Summarize a file
alias summarize='cat $1 | llf chat --cli "Summarize this"'

# Check system health
alias health='top -l 1 | head -10 | llf chat --cli "Is my system healthy?"'

# Git commit message generator
alias gitmsg='git diff --staged | llf chat --cli "Generate a concise commit message for these changes"'
```

**Usage:**
```bash
ask "How do I create a tar.gz file?"
explain
summarize report.txt
health
gitmsg
```

### Example 4: Monitoring Scripts

**Create `check_disk.sh`:**
```bash
#!/bin/bash
# Monitor disk space and get LLM recommendations

DISK_USAGE=$(df -h)
ANALYSIS=$(echo "$DISK_USAGE" | llf chat --auto-start-server --cli "Analyze this disk usage. Should I take action? Be concise.")

echo "=== Disk Usage Analysis ==="
echo "$DISK_USAGE"
echo ""
echo "=== LLM Analysis ==="
echo "$ANALYSIS"

# Optional: Send alert if LLM detects issues
if echo "$ANALYSIS" | grep -qi "critical\|urgent\|immediate"; then
    echo "⚠️  ALERT: Immediate action needed!"
    # Send notification, email, etc.
fi
```

### Example 5: Log Monitoring

**Create `monitor_logs.sh`:**
```bash
#!/bin/bash
# Monitor logs and alert on anomalies

LOG_FILE="/var/log/application.log"
LAST_LINES=$(tail -50 "$LOG_FILE")

ALERT=$(echo "$LAST_LINES" | llf chat --cli "Analyze these logs. Are there critical errors? Reply with YES or NO first, then explain.")

if echo "$ALERT" | grep -q "^YES"; then
    echo "🚨 Alert detected in logs!"
    echo "$ALERT"
    # Send notification
fi
```

### Example 6: Automated Code Review

**Create `review_changes.sh`:**
```bash
#!/bin/bash
# Review git changes before committing

if ! git diff --staged --quiet; then
    echo "Analyzing staged changes..."
    git diff --staged | llf chat --auto-start-server --cli "Review this code for bugs, security issues, and best practices. Be concise but thorough."
else
    echo "No staged changes to review."
fi
```

**Usage:**
```bash
git add .
./review_changes.sh
# Review LLM feedback
git commit -m "Your message"
```

---

## LLM-Powered Scripts

Complete scripts showcasing LLM integration.

### Script 1: Smart File Organizer

**Create `organize_files.sh`:**
```bash
#!/bin/bash
# Use LLM to suggest file organization

echo "Analyzing current directory structure..."
STRUCTURE=$(ls -lah)

SUGGESTION=$(echo "$STRUCTURE" | llf chat --auto-start-server --cli "Analyze these files and suggest how to organize them into folders. Provide specific folder names and which files go where.")

echo "=== LLM Organization Suggestion ==="
echo "$SUGGESTION"
echo ""
echo "Would you like to apply this organization? (y/n)"
read -r APPLY

if [ "$APPLY" = "y" ]; then
    echo "Generating organization script..."

    SCRIPT=$(llf chat --cli "Based on your previous suggestion, generate a bash script to organize these files. Include mkdir and mv commands. Script only, no explanation.")

    echo "Script to execute:"
    echo "$SCRIPT"
    echo ""
    echo "Execute this script? (y/n)"
    read -r EXECUTE

    if [ "$EXECUTE" = "y" ]; then
        eval "$SCRIPT"
        echo "✅ Files organized!"
    fi
fi
```

### Script 2: Intelligent Backup Selector

**Create `smart_backup.sh`:**
```bash
#!/bin/bash
# LLM helps decide what to backup

echo "Analyzing files for backup importance..."

FILE_LIST=$(find . -type f -exec ls -lh {} \; | head -50)

BACKUP_PLAN=$(echo "$FILE_LIST" | llf chat --auto-start-server --cli "Which of these files are most important to backup? Consider file types, sizes, and likely content. List the most critical files.")

echo "=== Recommended Backup List ==="
echo "$BACKUP_PLAN"

# Extract filenames and create backup
echo ""
echo "Create tar backup of these files? (y/n)"
read -r CREATE

if [ "$CREATE" = "y" ]; then
    BACKUP_FILES=$(echo "$BACKUP_PLAN" | grep -oE '\./[^ ]+' | tr '\n' ' ')
    tar -czf "backup_$(date +%Y%m%d_%H%M%S).tar.gz" $BACKUP_FILES
    echo "✅ Backup created!"
fi
```

### Script 3: Documentation Generator

**Create `gen_docs.sh`:**
```bash
#!/bin/bash
# Generate documentation for a project

PROJECT_STRUCTURE=$(tree -L 2 -I 'node_modules|venv|__pycache__')
README_EXISTS=$(test -f README.md && echo "yes" || echo "no")

if [ "$README_EXISTS" = "yes" ]; then
    echo "Analyzing existing README..."
    CURRENT_README=$(cat README.md)

    SUGGESTIONS=$(echo "$CURRENT_README" | llf chat --auto-start-server --cli "Review this README. What's missing? What could be improved?")

    echo "=== README Improvement Suggestions ==="
    echo "$SUGGESTIONS"
else
    echo "No README found. Generating one..."

    NEW_README=$(echo "$PROJECT_STRUCTURE" | llf chat --auto-start-server --cli "Create a README.md for this project structure. Include sections for: Description, Installation, Usage, Project Structure, Contributing.")

    echo "$NEW_README" > README.md
    echo "✅ README.md created!"
    cat README.md
fi
```

### Script 4: Error Explainer

**Create `explain_error.sh`:**
```bash
#!/bin/bash
# Explain the last command error

LAST_EXIT=$?
LAST_CMD=$(fc -ln -1)

if [ $LAST_EXIT -ne 0 ]; then
    echo "Last command failed with exit code $LAST_EXIT"
    echo "Command: $LAST_CMD"
    echo ""
    echo "Asking LLM for help..."

    EXPLANATION=$(llf chat --auto-start-server --cli "This command failed: '$LAST_CMD' with exit code $LAST_EXIT. What went wrong and how do I fix it?")

    echo "=== LLM Explanation ==="
    echo "$EXPLANATION"
else
    echo "Last command succeeded!"
fi
```

**Add to `~/.bashrc`:**
```bash
alias why='bash ~/explain_error.sh'
```

**Usage:**
```bash
rm /protected/file  # Fails with permission error
why                  # LLM explains the error and solution
```

### Script 5: Data Transformer

**Create `transform_data.sh`:**
```bash
#!/bin/bash
# Transform data between formats using LLM

INPUT_FILE=$1
OUTPUT_FORMAT=$2

if [ -z "$INPUT_FILE" ] || [ -z "$OUTPUT_FORMAT" ]; then
    echo "Usage: $0 <input_file> <output_format>"
    echo "Example: $0 data.csv json"
    exit 1
fi

echo "Transforming $INPUT_FILE to $OUTPUT_FORMAT..."

CONTENT=$(cat "$INPUT_FILE")
TRANSFORMED=$(echo "$CONTENT" | llf chat --auto-start-server --cli "Transform this data to $OUTPUT_FORMAT format. Output ONLY the transformed data, no explanations.")

OUTPUT_FILE="${INPUT_FILE%.*}.$OUTPUT_FORMAT"
echo "$TRANSFORMED" > "$OUTPUT_FILE"

echo "✅ Transformed data saved to $OUTPUT_FILE"
```

**Usage:**
```bash
./transform_data.sh data.csv json
./transform_data.sh config.json yaml
```

---

## Combining Features for Maximum Power

Combine chat, memory, data stores, and modules for incredible workflows!

### Workflow 1: Personal Research Assistant

**Setup:**
```bash
# 1. Enable memory for persistent knowledge
llf memory enable main_memory

# 2. Attach your research data stores
llf datastore attach research_papers
llf datastore attach documentation

# 3. Start chatting
llf chat --auto-start-server
```

**Usage:**
```
You: Search the research papers for information about neural networks

LLM: [Searches data store]
     Based on the attached research papers, here's what I found about neural networks...
     [Provides detailed answer with sources]

     [LLM also saves key insights to memory for future reference]

You: Remember that I'm focusing on computer vision applications

LLM: I'll remember that you're interested in computer vision applications of neural networks.
     [Saves preference to memory]
```

**Next session:**
```
You: What were we researching?

LLM: [Searches memory]
     You're researching neural networks, specifically focused on computer vision applications.
     Would you like to continue exploring this topic?
```

### Workflow 2: Voice-Enabled System Monitor

**Setup:**
```bash
# 1. Enable speech modules
llf module enable text2speech
llf module enable speech2text

# 2. Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
    STATS=$(top -l 1 | head -10)
    ANALYSIS=$(echo "$STATS" | llf chat --auto-start-server --cli "Summarize system health in one sentence")
    echo "$ANALYSIS"
    # LLM speaks the analysis (text2speech enabled)
    sleep 60
done
EOF
chmod +x monitor.sh

# 3. Run monitor
./monitor.sh
```

**Result:**
- System checks every 60 seconds
- LLM analyzes and summarizes
- Speaks results out loud
- Hands-free monitoring!

### Workflow 3: Code Learning System

**Setup:**
```bash
# 1. Create code knowledge data store
cd bin/tools/data_store
./Process_PDF.py -i python_documentation.pdf -o python_docs.jsonl -f jsonl

# 2. Create vector store
./Create_VectorStore.py -i python_docs.jsonl -o ../../data_stores/python_knowledge \
    -m sentence-transformers/all-mpnet-base-v2 -c 1500 -v 250

# 3. Register and attach
llf datastore attach python_knowledge

# 4. Enable memory for learning tracking
llf memory enable learning_progress
```

**Usage:**
```bash
# Ask questions about Python
llf chat

You: How do I use list comprehensions?

LLM: [Searches python_knowledge data store]
     According to the documentation, list comprehensions provide a concise way to create lists...
     [Detailed explanation with examples]

     [Saves "learned list comprehensions" to memory]

You: Remember I'm learning Python for data analysis

LLM: I'll remember you're learning Python for data analysis.
     [Saves context to memory]
```

### Workflow 4: Smart Documentation Browser

**Create `doc_search.sh`:**
```bash
#!/bin/bash
# Search documentation with context

QUERY="$1"

if [ -z "$QUERY" ]; then
    echo "Usage: $0 'your question'"
    exit 1
fi

# Ensure documentation data store is attached
llf datastore attach technical_docs 2>/dev/null

# Query with memory context
ANSWER=$(llf chat --auto-start-server --cli "Search the technical docs for: $QUERY. Be concise and include relevant code examples.")

echo "=== Answer ==="
echo "$ANSWER"

# Save to memory for reference
llf chat --auto-start-server --cli "Remember: User asked about '$QUERY' and was interested in this topic" >/dev/null
```

**Usage:**
```bash
./doc_search.sh "How to configure nginx reverse proxy"
./doc_search.sh "Docker compose networking"
```

---

## Fun with Memory

Creative ways to use the memory system.

### Idea 1: Personal Knowledge Base

**Build your knowledge over time:**

```
You: Remember that I prefer Python over JavaScript for backend development

LLM: I'll remember your preference for Python over JavaScript for backend work.

You: Remember my favorite text editor is VS Code

LLM: Noted - your favorite text editor is VS Code.

You: Remember I'm currently learning Docker and Kubernetes

LLM: I've saved that you're currently learning Docker and Kubernetes.
```

**Later:**
```
You: What should I learn next based on what you know about me?

LLM: [Searches memory]
     Based on what I know:
     - You prefer Python for backend
     - You use VS Code
     - You're learning Docker and Kubernetes

     I'd suggest learning:
     1. FastAPI or Django for Python web apps
     2. Helm for Kubernetes package management
     3. CI/CD with GitHub Actions
```

### Idea 2: Task Tracker

**Use memory as a task manager:**

```bash
# Add tasks
llf chat --cli "Remember task: Write documentation for the API"
llf chat --cli "Remember task: Fix bug in user authentication"
llf chat --cli "Remember task: Review pull request #42"

# Check tasks
llf chat --cli "What tasks do I have to do?"

# Mark complete
llf chat --cli "I completed the documentation task"
```

### Idea 3: Meeting Notes

**After meetings, save key points:**

```bash
# Save meeting notes
cat meeting_notes.txt | llf chat --auto-start-server --cli "Remember the key decisions and action items from this meeting"

# Later, recall
llf chat --cli "What did we decide in the last project meeting?"
```

### Idea 4: Code Snippet Library

**Save useful commands:**

```
You: Remember: To kill a process on port 3000, use: lsof -ti:3000 | xargs kill -9

LLM: I've saved that command for killing processes on port 3000.

You: Remember: To create a Python virtual environment: python -m venv venv && source venv/bin/activate

LLM: Saved the Python virtual environment creation command.
```

**Recall later:**
```
You: How do I kill a process on a specific port?

LLM: [Searches memory]
     To kill a process on port 3000, use: lsof -ti:3000 | xargs kill -9
```

---

## Fun with Data Stores (RAG)

Use RAG data stores for specialized knowledge.

### Idea 1: Personal Documentation Library

**Setup:**
```bash
# Download PDFs of documentation you frequently reference
# AWS docs, Python docs, Framework guides, etc.

# Convert to JSONL
cd bin/tools/data_store
for pdf in ~/Downloads/docs/*.pdf; do
    ./Process_PDF.py -i "$pdf" -o "$(basename "$pdf" .pdf).jsonl" -f jsonl
done

# Create vector store
./Create_VectorStore.py -i *.jsonl -o ../../data_stores/my_docs \
    -m sentence-transformers/all-mpnet-base-v2 -c 1500 -v 250

# Attach
llf datastore attach my_docs
```

**Usage:**
```bash
llf chat

You: How do I configure AWS S3 bucket policies?

LLM: [Searches my_docs data store]
     According to the AWS documentation in the data store, S3 bucket policies...
     [Provides detailed answer with examples from your docs]
```

### Idea 2: Company Knowledge Base

**Create a company-wide knowledge base:**

```bash
# Convert company docs, wikis, procedures
cd bin/tools/data_store

# Process various formats
./Process_PDF.py -i company_handbook.pdf -o handbook.jsonl -f jsonl
./Process_DOC.py -i procedures.docx -o procedures.jsonl -f jsonl
./Process_WEB.py -i https://company-wiki.com/engineering -o wiki.jsonl -f jsonl

# Create vector store
./Create_VectorStore.py -i *.jsonl -o ../../data_stores/company_knowledge \
    -m sentence-transformers/all-mpnet-base-v2 -c 1500 -v 250

# Attach
llf datastore attach company_knowledge
```

**Usage:**
```
You: What's our company's code review process?

LLM: [Searches company_knowledge]
     According to the engineering procedures document...
```

### Idea 3: Research Paper Analysis

**Load research papers:**

```bash
cd bin/tools/data_store

# Process multiple research papers
for pdf in ~/Papers/*.pdf; do
    ./Process_PDF.py -i "$pdf" -o "$(basename "$pdf" .pdf).jsonl" -f jsonl
done

# Create specialized vector store for academic content
./Create_VectorStore.py -i *.jsonl -o ../../data_stores/research_papers \
    -m sentence-transformers/all-mpnet-base-v2 -c 2000 -v 300

llf datastore attach research_papers
```

**Usage:**
```
You: Summarize the key findings about transformer architectures across all papers

LLM: [Searches all research papers in data store]
     Analyzing the research papers, here are the key findings about transformers:

     1. From "Attention Is All You Need" (Vaswani et al.)...
     2. From "BERT: Pre-training..." (Devlin et al.)...
     [Comprehensive summary with citations]
```

### Idea 4: Codebase Documentation

**Document your own code:**

```bash
# Generate documentation from your codebase
cd bin/tools/data_store

# Convert code comments and READMEs
find ~/Projects/my-app -name "*.md" -o -name "*.py" | while read file; do
    ./Process_TXT.py -i "$file" -o "$(basename "$file").jsonl" -f jsonl
done

# Create vector store
./Create_VectorStore.py -i *.jsonl -o ../../data_stores/my_codebase \
    -m jinaai/jina-embeddings-v2-base-code -c 3000 -v 500

llf datastore attach my_codebase
```

**Usage:**
```
You: How does the authentication system work in my codebase?

LLM: [Searches my_codebase data store]
     Based on your code documentation, the authentication system...
```

---

## Fun with Modules

Creative uses for speech and other modules.

### Idea 1: Hands-Free Coding Assistant

**Setup:**
```bash
# Enable both speech modules
llf module enable text2speech
llf module enable speech2text

# Start chat
llf chat --auto-start-server
```

**Usage:**
```
[Speak]: "How do I create a Python decorator?"

[LLM speaks back]: "A Python decorator is a function that modifies another function.
                    Here's an example: [provides code example]"
```

**Perfect for:**
- Coding while looking at documentation
- Learning while exercising
- Accessibility
- Multitasking

### Idea 2: Code Review Announcer

**Create `announce_review.sh`:**
```bash
#!/bin/bash
# Reviews code and announces findings

# Enable TTS module
llf module enable text2speech

CODE_FILE="$1"

if [ -z "$CODE_FILE" ]; then
    echo "Usage: $0 <code_file>"
    exit 1
fi

# Review code with speech output
cat "$CODE_FILE" | llf chat --auto-start-server --cli "Review this code and list the top 3 issues found. Be concise."

# LLM speaks the review!
```

**Usage:**
```bash
./announce_review.sh app.py
# LLM reviews and speaks: "I found three issues: 1. Missing error handling..."
```

### Idea 3: Walking Debugger

**Debug while walking around:**

```bash
# Enable speech modules
llf module enable text2speech
llf module enable speech2text

# Start chat
llf chat

[Speak]: "Here's my error: [read error message]"
[LLM speaks]: "This error occurs because..."

[Speak]: "How do I fix it?"
[LLM speaks]: "Try adding a null check before..."
```

**Benefits:**
- Move around while debugging
- Think while walking
- No typing needed

### Idea 4: Learning Companion

**Interactive learning with voice:**

```bash
# Enable modules
llf module enable text2speech
llf module enable speech2text

# Attach learning data store
llf datastore attach python_tutorial

# Enable memory to track progress
llf memory enable learning_progress

# Start learning
llf chat
```

**Interaction:**
```
[Speak]: "Teach me about list comprehensions"
[LLM speaks]: "List comprehensions provide a concise way to create lists..."

[Speak]: "Give me an example"
[LLM speaks]: "Here's an example: numbers = [x for x in range(10)]..."

[Speak]: "Quiz me on this"
[LLM speaks]: "Sure! How would you create a list of squares from 1 to 10?"

[Speak]: "squares = [x*x for x in range(1, 11)]"
[LLM speaks]: "Excellent! That's correct. You've mastered list comprehensions!"
```

---

## Real-World Workflows

Complete workflows combining everything.

### Workflow 1: Daily Developer Assistant

**Morning setup script `dev_start.sh`:**
```bash
#!/bin/bash
# Start your AI-powered dev day

echo "🚀 Starting AI Development Assistant..."

# 1. Enable memory for context
llf memory enable dev_memory

# 2. Attach relevant documentation
llf datastore attach project_docs
llf datastore attach api_reference

# 3. Start server
llf server start --daemon

# 4. Morning briefing
echo ""
echo "=== Morning Briefing ==="
llf chat --cli "What tasks did I say I would work on yesterday?"

echo ""
echo "=== Git Status ==="
git status | llf chat --cli "Summarize my git status. What should I focus on?"

echo ""
echo "=== Recent Changes ==="
git log --oneline -5 | llf chat --cli "What have I been working on recently?"

echo ""
echo "✅ Ready to code! Start chatting with: llf chat"
```

### Workflow 2: Code Review Pipeline

**Create `.git/hooks/pre-commit`:**
```bash
#!/bin/bash
# AI-powered pre-commit hook

echo "🔍 Running AI code review..."

CHANGES=$(git diff --staged)

if [ -n "$CHANGES" ]; then
    REVIEW=$(echo "$CHANGES" | llf chat --auto-start-server --cli "Quick code review: Any critical issues? Reply YES or NO first, then explain briefly.")

    echo "$REVIEW"

    if echo "$REVIEW" | grep -q "^YES"; then
        echo ""
        echo "⚠️  Critical issues found! Commit anyway? (y/n)"
        read -r CONTINUE

        if [ "$CONTINUE" != "y" ]; then
            echo "❌ Commit cancelled"
            exit 1
        fi
    fi
fi

echo "✅ Code review passed"
```

### Workflow 3: Documentation Automation

**Create `update_docs.sh`:**
```bash
#!/bin/bash
# Automatically update documentation based on code changes

# 1. Analyze what changed
CHANGES=$(git diff HEAD~1 --name-only)

echo "Files changed: $CHANGES"

# 2. Ask LLM what docs need updating
DOCS_NEEDED=$(echo "$CHANGES" | llf chat --auto-start-server --cli "These files changed. What documentation should be updated?")

echo "=== Documentation Updates Needed ==="
echo "$DOCS_NEEDED"

# 3. Generate documentation
for file in $CHANGES; do
    if [[ $file == *.py ]]; then
        echo "Generating docs for $file..."

        DOC=$(cat "$file" | llf chat --cli "Generate API documentation for this Python code. Include function descriptions, parameters, and return values.")

        DOC_FILE="docs/$(basename "$file" .py).md"
        echo "$DOC" > "$DOC_FILE"

        echo "✅ Created $DOC_FILE"
    fi
done
```

### Workflow 4: Intelligent Log Monitoring

**Create `smart_monitor.sh`:**
```bash
#!/bin/bash
# Continuously monitor logs with AI analysis

LOG_FILE="/var/log/application.log"
CHECK_INTERVAL=300  # 5 minutes

# Enable memory to track patterns
llf memory enable monitoring_memory

# Enable TTS for alerts
llf module enable text2speech

echo "🔍 Starting intelligent log monitoring..."
echo "Monitoring: $LOG_FILE"
echo "Check interval: ${CHECK_INTERVAL}s"

while true; do
    # Get recent logs
    RECENT_LOGS=$(tail -100 "$LOG_FILE")

    # Analyze with context from memory
    ANALYSIS=$(echo "$RECENT_LOGS" | llf chat --auto-start-server --cli "Analyze these logs for anomalies, errors, or unusual patterns. Check memory for known issues. Be concise.")

    # Check for critical issues
    if echo "$ANALYSIS" | grep -qi "critical\|urgent\|error\|failure"; then
        echo "🚨 ALERT: Critical issue detected!"
        echo "$ANALYSIS"

        # LLM speaks the alert
        echo "$ANALYSIS" | llf chat --cli "Summarize this alert in one sentence for voice announcement"

        # Optional: Send notification
        # send_notification "$ANALYSIS"
    else
        echo "[$(date)] Status: Normal"
    fi

    sleep $CHECK_INTERVAL
done
```

### Workflow 5: Personal Productivity System

**Create `productivity.sh`:**
```bash
#!/bin/bash
# AI-powered productivity assistant

# Enable memory for task tracking
llf memory enable productivity_memory

# Enable voice for hands-free
llf module enable text2speech
llf module enable speech2text

function morning_routine() {
    echo "☀️ Good morning! Planning your day..."

    llf chat --auto-start-server --cli "What tasks do I have for today? List them by priority."

    echo ""
    echo "What would you like to focus on first?"
}

function add_task() {
    llf chat --auto-start-server --cli "Remember task: $1"
    echo "✅ Task added: $1"
}

function check_progress() {
    llf chat --auto-start-server --cli "What tasks have I completed today? What's left?"
}

function end_of_day() {
    echo "🌙 End of day review..."

    llf chat --auto-start-server --cli "Summarize what I accomplished today and what's pending for tomorrow"
}

# Main menu
case "$1" in
    morning)
        morning_routine
        ;;
    add)
        shift
        add_task "$@"
        ;;
    check)
        check_progress
        ;;
    evening)
        end_of_day
        ;;
    *)
        echo "Usage: $0 {morning|add|check|evening}"
        echo ""
        echo "Commands:"
        echo "  morning  - Morning planning"
        echo "  add      - Add a task"
        echo "  check    - Check progress"
        echo "  evening  - End of day review"
        ;;
esac
```

**Usage:**
```bash
./productivity.sh morning
./productivity.sh add "Write unit tests for authentication"
./productivity.sh check
./productivity.sh evening
```

---

## Chat session history and re-use

All chat conversations are saved locally under `configs/chat_history` unless the `--no-history` parameter is added to the `llf chat` command

### Enable and Disable chat history

By default all chat conversations are saved locally in a JSON formatted document in `configs/chat_history`. 

You can use the `--no-history` parmeter to disable logging for the current session
```bash
llf chat --no-history
```

### Viewing chat logs
You can run the following command to view the chat log information
```bash
llf chat history list
```

**Example Output:**
```
SESSION ID             ┃ DATE                ┃ MESSAGES ┃ MODEL
20260114_162050_159296 │ 2026-01-14 16:20:50 │ 2        │ Qwen/Qwen2.5-32B-Instruct-GGUF
20260114_162021_248062 │ 2026-01-14 16:20:21 │ 4        │ Qwen/Qwen2.5-32B-Instruct-GGUF
```

You can run the following command to view the details of one of the chat logs
```bash
llf chat history info 20260114_162021_248062
```

NOTE:  The output will generate the detailed information of the chat engagement with the LLM during that session

### Continue an old conversation with the LLM

You can load one of the chat logs with the LLM which will make the conversation engagement continue where you left off from the log perspective
```bash
llf chat --continue-session 20260114_162021_248062
```

You can specify any SESSION ID, to continue a conversation.

### Export chat log data

You can export the chat sessions to an external file.  The following exported file types are supported
- txt
- json
- md
- pdf

Lets export the SESSION ID `20260114_162021_248062` and save it to a JSON document
```bash
llf chat export 20260114_162021_248062 --format json --output my_chat.json
```

Take the content of the JSON file and load it into a local chat to use
```bash
llf chat --import-session my_chat.json
```

---

## Tips and Tricks

Quick tips to level up your LLM usage.

### Tip 1: Use Short Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Quick LLM access
alias ai='llf chat --auto-start-server --cli'
alias aia='llf chat --auto-start-server'  # Auto-start interactive

# System helpers
alias wtf='fc -ln -1 | ai "Explain this command"'
alias howto='ai'
alias analyze='ai "Analyze this:"'

# Git helpers
alias githelp='git status | ai "What should I do next?"'
alias commitmsg='git diff --staged | ai "Generate a commit message"'

# File helpers
alias summarize='ai "Summarize this file:"'
alias explain='ai "Explain this code:"'
```

### Tip 2: Combine with External APIs

**Use ChatGPT for complex tasks:**

```bash
# In config.json, switch to OpenAI
# Then use for heavy reasoning tasks

cat complex_problem.txt | llf chat --cli "Solve this step by step"
```

**Use Claude for long documents:**

```bash
# In config.json, switch to Anthropic
# Then use for document analysis

cat long_document.pdf | llf chat --cli "Analyze this thoroughly"
```

**Switch back to local for fast queries:**

```bash
# In config.json, switch back to local server
# Use for quick, private queries

llf chat --cli "Quick question: what's 15% of 380?"
```

### Tip 3: Create Domain-Specific Prompts

**For coding (edit `config_prompt.json`):**
```json
{
  "system_prompt": "You are a senior software engineer. Always provide:\n1. Working code examples\n2. Best practices\n3. Common pitfalls to avoid\n4. Performance considerations"
}
```

**For writing (edit `config_prompt.json`):**
```json
{
  "system_prompt": "You are a professional editor. Help improve:\n1. Clarity and conciseness\n2. Grammar and style\n3. Structure and flow\n4. Tone consistency"
}
```

**Switch between them:**
```bash
cp config_prompt.json config_prompt_code.json
cp config_prompt_write.json config_prompt.json
# Restart chat for changes to take effect
```

### Tip 4: Build a Personal Command Library

**Create `~/.llm_commands/`:**

```bash
mkdir -p ~/.llm_commands
cd ~/.llm_commands

# Create specialized scripts
cat > explain_error.sh << 'EOF'
#!/bin/bash
llf chat --auto-start-server --cli "Explain this error and how to fix: $1"
EOF

cat > code_review.sh << 'EOF'
#!/bin/bash
cat "$1" | llf chat --auto-start-server --cli "Review this code"
EOF

cat > generate_tests.sh << 'EOF'
#!/bin/bash
cat "$1" | llf chat --auto-start-server --cli "Generate pytest unit tests for this code"
EOF

chmod +x *.sh
```

**Add to PATH:**
```bash
echo 'export PATH="$HOME/.llm_commands:$PATH"' >> ~/.bashrc
```

### Tip 5: Use JSON for Structured Output

**Request JSON responses:**

```bash
llf chat --cli "List the 3 largest files in /var/log as JSON with fields: name, size, date"
```

**Parse with jq:**

```bash
llf chat --cli "List the 3 largest files as JSON" | jq '.[] | select(.size > 1000000)'
```

**Use in scripts:**

```bash
RESPONSE=$(llf chat --cli "Analyze disk usage. Reply with JSON: {status: ok/warning/critical, message: string}")

STATUS=$(echo "$RESPONSE" | jq -r '.status')

if [ "$STATUS" = "critical" ]; then
    # Send alert
    echo "Critical disk usage!"
fi
```

---

## Summary

You've learned creative and practical ways to use your LLM beyond basic chat!

### Key Takeaways

1. **Customize Personality**
   - Edit `config_prompt.json`
   - Create domain-specific assistants
   - Pirate, teacher, reviewer, or professional

2. **CLI Mode for Automation**
   - `llf chat --cli "question"`
   - Perfect for scripts
   - Combine with `--auto-start-server`

3. **Pipe Data for Analysis**
   - `command | llf chat --cli "analyze this"`
   - Logs, files, system info
   - Real-time analysis

4. **Build Smart Scripts**
   - Generate commands
   - Monitor systems
   - Automate reviews
   - Create documentation

5. **Combine Features**
   - Memory + Chat = Personal assistant
   - Data Stores + Chat = Knowledge expert
   - Modules + Chat = Voice interaction
   - All together = Powerful workflows

6. **Real Workflows**
   - Daily dev assistant
   - Code review automation
   - Log monitoring
   - Productivity system

### Quick Command Reference

```bash
# Basic chat
llf chat
llf chat --auto-start-server

# CLI mode
llf chat --cli "question"

# Pipe data
cat file.txt | llf chat --cli "summarize"
ps aux | llf chat --cli "what uses most memory?"

# Capture output
ANSWER=$(llf chat --cli "command for finding large files")

# With memory
llf memory enable main_memory
llf chat --cli "remember my preference"

# With data stores
llf datastore attach docs
llf chat --cli "search docs for X"

# With speech
llf module enable text2speech
llf chat  # LLM speaks responses
```

### Next Steps

1. **Experiment with prompts** - Create your perfect AI assistant
2. **Build personal scripts** - Automate your workflow
3. **Create data stores** - Add specialized knowledge
4. **Enable memory** - Build persistent context
5. **Try voice mode** - Hands-free interaction
6. **Combine features** - Build powerful workflows

### Related Documentation

- [Basic User Guide](../Basic_User_Guide.md) - Getting started
- [Setup Memory](Setup_Memory.md) - Persistent knowledge
- [Setup Data Stores](Setup_Datastore_RAG.md) - RAG system
- [Setup Talking](Setup_Talking.md) - Voice modules
- [Setup External LLM](Setup_External_LLM.md) - Use ChatGPT/Claude

---

**The only limit is your imagination!** 🚀

Experiment, create, and discover new ways to use your LLM. Share your cool discoveries and workflows with the community!
