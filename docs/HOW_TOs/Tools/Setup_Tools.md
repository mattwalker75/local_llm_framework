
# Use and Develop Tools

Enable and create tools that extend the **functionality and capabilities of the LLM** beyond text generation. Tools enable the LLM to interact with external systems, access files, execute commands, search the internet, and more.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Available Tools](#available-tools)
3. [Tool Usage Examples](#tool-usage-examples)
4. [Creating New Tools](#creating-new-tools)
5. [Tool Security](#tool-security)
6. [Testing Tools](#testing-tools)

---

## Architecture Overview

### How Tools Work (High-Level)

```
┌─────────┐      ┌─────────┐      ┌──────────────┐      ┌────────┐
│  User   │ ───> │   LLM   │ ───> │ Tool Execute │ ───> │ System │
│ Request │      │Analysis │      │   (Secure)   │      │ Action │
└─────────┘      └─────────┘      └──────────────┘      └────────┘
                      │                   │
                      │                   v
                      │            ┌─────────────┐
                      └<────────── │   Results   │
                                   └─────────────┘
```

**Step-by-Step**:
1. **User Request**: User asks LLM to perform an action
2. **LLM Analysis**: LLM determines which tool(s) to use
3. **Tool Invocation**: LLM calls tool with structured arguments (JSON)
4. **Security Check**: Framework validates whitelist, permissions, dangerous operations
5. **Execution**: Tool executes the operation (file read, command, API call, etc.)
6. **Results**: Tool returns results to LLM
7. **Response**: LLM integrates results into natural language response

### Tool Types

- **llm_invokable**: Tools the LLM can call directly during conversation
- **preprocessor**: Tools that modify input before sending to the LLM
- **postprocessor**: Tools that modify LLM output before showing to the user

### Tool Registry (`tools_registry.json`)

All tools are registered in the registry. Each tool entry contains:

```json
{
  "name": "file_access",
  "display_name": "File Access Tool",
  "type": "llm_invokable",
  "enabled": false,
  "directory": "file_access",
  "metadata": {
    "category": "file_operations",
    "mode": "ro",
    "root_dir": ".",
    "whitelist": [],
    "requires_approval": false
  }
}
```

---

## Available Tools

### 1. Command Execution (`command_exec`) ⚠️

**Purpose**: Execute shell commands with whitelist-based security

**Status**: Disabled by default (security-sensitive)

**Use Cases**:
- Running build scripts (`npm run build`, `make`, etc.)
- Git operations (`git status`, `git commit`, etc.)
- System diagnostics (`ls`, `pwd`, `df`, etc.)
- Package management (`npm install`, `pip install`, etc.)

**Security Features**:
- ✅ Whitelist-only command execution (glob patterns supported)
- ✅ Dangerous command detection (`rm`, `del`, `format`, `mkfs`, `dd`)
- ✅ Timeout protection (1-300 seconds, default 30s)
- ✅ No shell injection (commands run with `subprocess.run(shell=False)`)
- ✅ Comprehensive logging of all command executions

**Configuration**:
```json
{
  "metadata": {
    "whitelist": ["git*", "npm*", "ls", "pwd"],
    "requires_approval": false
  }
}
```

---

### 2. File Access (`file_access`) ⚠️

**Purpose**: Read, write, and list files with whitelist protection

**Status**: Disabled by default (security-sensitive)

**Use Cases**:
- Reading configuration files
- Writing logs, reports, or generated code
- Listing directory contents
- Creating/editing documentation

**Security Features**:
- ✅ Whitelist patterns (glob: `*.txt`, fully qualified: `/path/to/file`)
- ✅ Mode-based permissions: `ro` (read-only) or `rw` (read-write)
- ✅ Root directory restriction (chroot-like containment)
- ✅ Dangerous path detection (system files, SSH keys, credentials, etc.)
- ✅ 10MB file size limit
- ✅ Path traversal prevention

**Configuration**:
```json
{
  "metadata": {
    "mode": "ro",
    "root_dir": "/home/user/project",
    "whitelist": ["*.py", "*.md", "docs/*"],
    "requires_approval": false
  }
}
```

**Operations**:
- `read`: Read file contents
- `write`: Create or overwrite file (requires `rw` mode)
- `list`: List files in directory

---

### 3. Internet Search - DuckDuckGo (`internet_duckduckgo`)

**Purpose**: Search the internet using DuckDuckGo (privacy-focused, no API key)

**Status**: Disabled by default

**Use Cases**:
- Finding current information
- Researching topics
- Looking up documentation
- Fact-checking
- News and trends

**Features**:
- ✅ Free (no API key required)
- ✅ Privacy-focused (no tracking)
- ✅ Returns 1-20 results (configurable)
- ✅ Includes title, URL, and snippet for each result
- ✅ Clean, ad-free results

**Dependencies**: `ddgs` or `duckduckgo-search`

**Example Result**:
```json
{
  "success": true,
  "query": "Python 3.13 features",
  "num_results": 5,
  "results": [
    {
      "title": "What's New In Python 3.13",
      "url": "https://docs.python.org/3.13/whatsnew/3.13.html",
      "snippet": "Python 3.13 introduces improved performance..."
    }
  ]
}
```

---

### 4. Internet Search - Google API (`internet_google_api`)

**Purpose**: Search using Google Custom Search API (requires API key)

**Status**: Disabled by default

**Use Cases**:
- High-quality search results
- Custom search engines
- Programmatic search with quotas

**Features**:
- ✅ High-quality results with Google's ranking
- ✅ Returns up to 10 results per query (Google API limit)
- ✅ Supports custom search parameters
- ✅ Structured JSON responses

**Requirements**:
- Google API Key (`GOOGLE_API_KEY` environment variable)
- Custom Search Engine ID (`GOOGLE_CSE_ID` environment variable)

**Dependencies**: `google-api-python-client`

**Setup**:
```bash
export GOOGLE_API_KEY="your-api-key"
export GOOGLE_CSE_ID="your-cse-id"
llf tool enable internet_google_api
```

---

### 5. Internet Search - Google Webscrape (`internet_google_webscrape`)

**Purpose**: Search Google by scraping results (no API key required)

**Status**: Disabled by default

**Use Cases**:
- Alternative when API key not available
- Quick searches without rate limits
- Ad-hoc research

**Features**:
- ✅ No API key required
- ✅ Returns 1-20 results
- ✅ Includes title, URL, and description
- ⚠️ May be rate-limited by Google
- ⚠️ Less reliable than API (subject to Google changes)

**Dependencies**: `googlesearch-python`

---

### 6. XML Formatting (`xml_format`)

**Purpose**: Format LLM output as valid XML (postprocessor)

**Status**: Enabled by default

**Use Cases**:
- Structured data output
- API responses
- Configuration files
- Data interchange formats

**Features**:
- ✅ Validates XML structure
- ✅ Formats with proper indentation
- ✅ Handles namespaces and attributes
- ✅ Automatic (runs as postprocessor)

**How It Works**: This tool runs automatically on LLM output. When the LLM generates XML, the formatter validates and prettifies it before showing to the user.

---

## Tool Usage Examples

### Example 1: Command Execution - Git Operations

**Scenario**: User wants to check git status and commit changes

**Setup**:
```bash
# Enable command_exec tool
llf tool enable command_exec

# Whitelist git commands
llf tool whitelist add command_exec "git*"
llf tool whitelist add command_exec "ls"
```

**Conversation**:
```
User: What's my current git status?

LLM: Let me check the git status for you.

     [LLM Decision: User wants git status → Use command_exec tool]
     [Tool Call: command_exec(command='git', arguments=['status'])]

     [Framework Security Check]
     ✓ Command 'git' matches whitelist pattern 'git*'
     ✓ 'git' is not a dangerous command
     ✓ Proceeding with execution...

     [Execution]
     $ git status
     On branch main
     Your branch is up to date with 'origin/main'.

     Changes not staged for commit:
       modified:   README.md
       modified:   src/main.py

     [Result returned to LLM]

     You're on the main branch and up to date with origin. You have
     two modified files:
     - README.md
     - src/main.py

User: Show me what files are in the current directory

LLM: [Tool Call: command_exec(command='ls', arguments=['-la'])]

     [Security Check: 'ls' in whitelist ✓]
     [Execution: ls -la]

     Here are the files in your current directory:
     - README.md (1.2 KB)
     - src/ (directory)
     - tests/ (directory)
     - package.json (456 bytes)
     ...
```

**High-Level Flow**:
1. User asks question requiring command execution
2. LLM recognizes need for `command_exec` tool
3. LLM constructs tool call with command and arguments
4. Framework validates command against whitelist
5. Framework checks for dangerous commands
6. Command executed using `subprocess.run(shell=False)` for security
7. stdout, stderr, and return code captured
8. Results sent back to LLM
9. LLM formats results naturally for user

---

### Example 2: File Access - Reading and Writing

**Scenario**: User wants to read a config file and create documentation

**Setup**:
```bash
# Enable file_access tool
llf tool enable file_access

# Configure for read-write mode and whitelist
# Edit tools_registry.json:
{
  "metadata": {
    "mode": "rw",
    "root_dir": "/home/user/myproject",
    "whitelist": [
      "*.md",
      "*.py",
      "config/*",
      "docs/*"
    ]
  }
}

# Or use CLI:
llf tool whitelist add file_access "*.md"
llf tool whitelist add file_access "*.py"
llf tool whitelist add file_access "config/*"
```

**Conversation**:
```
User: Read the config.json file

LLM: [Tool Call: file_access(operation='read', path='config/config.json')]

     [Framework Security Check]
     ✓ Path 'config/config.json' matches whitelist pattern 'config/*'
     ✓ Resolved to: /home/user/myproject/config/config.json
     ✓ Path is within root_dir
     ✓ Not a dangerous path
     ✓ File size: 2.1 KB (within 10MB limit)
     ✓ Operation 'read' allowed in 'rw' mode

     [File Read]
     {
       "app_name": "My Application",
       "version": "1.0.0",
       "database": {
         "host": "localhost",
         "port": 5432
       }
     }

     Here's your config.json content. It shows your app is version
     1.0.0 and uses a local PostgreSQL database on port 5432.

User: Create a README.md file documenting this configuration

LLM: I'll create a README.md file documenting your configuration.

     [Tool Call: file_access(
       operation='write',
       path='README.md',
       content='# My Application\n\nVersion: 1.0.0\n\n## Configuration...'
     )]

     [Security Check]
     ✓ Path 'README.md' matches whitelist pattern '*.md'
     ✓ Resolved to: /home/user/myproject/README.md
     ✓ Path is within root_dir
     ✓ Not a dangerous path
     ✓ Content size: 487 bytes (within limit)
     ✓ Operation 'write' allowed in 'rw' mode

     [File Write]
     File created successfully at /home/user/myproject/README.md

     I've created README.md with documentation about your application
     configuration. The file includes the version, database settings,
     and other key details.

User: What markdown files are in this directory?

LLM: [Tool Call: file_access(operation='list', path='.')]

     [Security Check & Execution]

     Found these markdown files:
     - README.md (487 bytes, modified 2 minutes ago)
     - CHANGELOG.md (1.2 KB, modified yesterday)
     - docs/API.md (3.4 KB, modified last week)
```

**High-Level Flow**:
1. User requests file operation
2. LLM determines which operation (read/write/list)
3. LLM calls `file_access` tool with operation and path
4. Framework resolves path relative to root_dir
5. Framework validates path against whitelist patterns
6. Framework checks dangerous paths (system files, credentials, etc.)
7. Framework checks mode permissions (ro vs rw)
8. Framework enforces 10MB size limit
9. Operation executed (read/write/list)
10. Results returned to LLM
11. LLM presents information naturally

---

### Example 3: Internet Search - Research

**Scenario**: User needs current information about a technology

**Setup**:
```bash
# Enable DuckDuckGo search (no API key needed)
llf tool enable internet_duckduckgo

# Or enable Google API (requires keys)
export GOOGLE_API_KEY="your-key"
export GOOGLE_CSE_ID="your-cse-id"
llf tool enable internet_google_api
```

**Conversation**:
```
User: What are the new features in Python 3.13?

LLM: Let me search for information about Python 3.13 features.

     [LLM Decision: Need current info → Use internet search]
     [Tool Call: search_internet_duckduckgo(
       query='Python 3.13 new features',
       max_results=5
     )]

     [Framework Execution]
     - Using ddgs library to search DuckDuckGo
     - Query: "Python 3.13 new features"
     - Max results: 5 (clamped to 1-20 range)

     [Search Results Received]
     1. What's New In Python 3.13 — Python 3.13 documentation
        https://docs.python.org/3.13/whatsnew/3.13.html
        Snippet: "Python 3.13 introduces improved performance with
        a Just-In-Time (JIT) compiler, better error messages..."

     2. Python 3.13 Released with JIT Compiler - Real Python
        https://realpython.com/python313-jit/
        Snippet: "The headline feature is experimental JIT compilation..."

     3. ...

     Based on my search, Python 3.13 has several major new features:

     **1. JIT Compiler (Experimental)**
     - Just-In-Time compilation for improved performance
     - Can significantly speed up certain workloads
     - Currently experimental, opt-in feature

     **2. Improved Error Messages**
     - More helpful traceback information
     - Better suggestions for fixing common errors

     **3. Performance Improvements**
     - Faster startup time
     - Reduced memory usage

     Sources:
     - [Official Python 3.13 Docs](https://docs.python.org/3.13/whatsnew/3.13.html)
     - [Real Python - Python 3.13 JIT](https://realpython.com/python313-jit/)

User: Search for "async/await best practices in Python"

LLM: [Tool Call: search_internet_duckduckgo(
       query='async await best practices Python',
       max_results=10
     )]

     [Results processed and synthesized...]

     I found several excellent resources on async/await best practices:
     ...
```

**High-Level Flow**:
1. User asks question requiring current/external information
2. LLM recognizes knowledge gap (beyond training data)
3. LLM formulates search query
4. LLM calls `search_internet_duckduckgo` with query and max_results
5. Framework uses ddgs library to search
6. Framework enforces max_results limits (1-20)
7. Results parsed (title, URL, snippet for each)
8. Results returned to LLM
9. LLM synthesizes information from multiple sources
10. LLM cites sources in response

**Why This Matters**: Without internet search, the LLM is limited to knowledge from its training data. With internet search, it can access current information, recent news, updated documentation, and real-time data.

---

### Example 4: XML Formatting (Automatic)

**Scenario**: User asks for structured data in XML format

**Setup**:
```bash
# xml_format is enabled by default as a postprocessor
llf tool list
# Shows: xml_format [enabled] (postprocessor)
```

**Conversation**:
```
User: Give me a list of users in XML format

LLM: [Generates XML content]

     [Before Postprocessor]
     <users><user id="1"><name>John</name><email>john@example.com</email></user><user id="2"><name>Jane</name><email>jane@example.com</email></user></users>

     [xml_format Postprocessor Runs Automatically]
     - Detects XML content
     - Validates structure
     - Formats with indentation
     - Ensures well-formed XML

     [After Postprocessor - Shown to User]
     <?xml version="1.0" encoding="UTF-8"?>
     <users>
       <user id="1">
         <name>John</name>
         <email>john@example.com</email>
       </user>
       <user id="2">
         <name>Jane</name>
         <email>jane@example.com</email>
       </user>
     </users>
```

**High-Level Flow**:
1. User requests XML output
2. LLM generates XML content
3. **Postprocessor automatically intercepts output**
4. XML formatter validates and prettifies
5. Formatted XML shown to user
6. No explicit tool call needed (transparent to LLM)

---

## Creating New Tools

### Complete Example: Weather API Tool

Let's create a new tool that fetches weather data.

#### Step 1: Create Directory Structure

```bash
mkdir tools/weather_api
cd tools/weather_api
```

#### Step 2: Create `config.json`

`tools/weather_api/config.json`:
```json
{
  "name": "weather_api",
  "display_name": "Weather API Tool",
  "type": "llm_invokable",
  "enabled": false,
  "directory": "weather_api",
  "metadata": {
    "category": "data_retrieval",
    "requires_approval": false,
    "api_key_required": true,
    "description": "Fetch current weather data for any location using WeatherAPI.com"
  }
}
```

#### Step 3: Create `__init__.py`

`tools/weather_api/__init__.py`:
```python
"""
Weather API Tool

Fetches current weather data for a specified location using WeatherAPI.com.

Example usage in conversation:
  User: "What's the weather in London?"
  LLM: [Calls get_weather(location='London')]
  Result: "London is currently 15°C and partly cloudy..."
"""

from typing import Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

# Tool definition for LLM - OpenAI function calling format
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather information for a location. Use this when the user asks about weather conditions, temperature, or forecast for any city or region.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or location (e.g., 'London', 'New York, NY', 'Tokyo, Japan', 'Paris, France')"
                },
                "units": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature units. Default is celsius."
                }
            },
            "required": ["location"]
        }
    }
}


def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute weather API request.

    Args:
        arguments: Dictionary containing:
            - location (str): City/location name
            - units (str, optional): 'celsius' or 'fahrenheit'

    Returns:
        Dictionary with format:
        {
            "success": bool,
            "location": str,
            "temperature": float,
            "condition": str,
            ...
        }
        OR on error:
        {
            "success": False,
            "error": str
        }
    """
    try:
        # Get API key from environment
        api_key = os.environ.get('WEATHER_API_KEY')
        if not api_key:
            return {
                "success": False,
                "error": "WEATHER_API_KEY environment variable not set. Get a free key at https://www.weatherapi.com/"
            }

        # Validate required inputs
        location = arguments.get('location')
        if not location:
            return {
                "success": False,
                "error": "Location parameter is required"
            }

        units = arguments.get('units', 'celsius')
        if units not in ['celsius', 'fahrenheit']:
            units = 'celsius'

        logger.info(f"Fetching weather for '{location}' in {units}")

        # Import requests (late import to avoid dependency if not installed)
        try:
            import requests
        except ImportError:
            return {
                "success": False,
                "error": "requests library not installed. Install with: pip install requests"
            }

        # Make API request to WeatherAPI.com
        url = "https://api.weatherapi.com/v1/current.json"
        params = {
            'key': api_key,
            'q': location,
            'aqi': 'no'  # Don't include air quality data
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract relevant weather data
        current = data.get('current', {})
        location_data = data.get('location', {})

        # Convert temperature if needed
        temp_c = current.get('temp_c', 0)
        temp = temp_c if units == 'celsius' else (temp_c * 9/5) + 32
        unit_symbol = '°C' if units == 'celsius' else '°F'

        # Build result
        result = {
            "success": True,
            "location": location_data.get('name'),
            "region": location_data.get('region'),
            "country": location_data.get('country'),
            "temperature": round(temp, 1),
            "temperature_display": f"{round(temp, 1)}{unit_symbol}",
            "condition": current.get('condition', {}).get('text'),
            "humidity": current.get('humidity'),
            "wind_speed_kph": current.get('wind_kph'),
            "wind_speed_mph": current.get('wind_mph'),
            "feels_like_c": current.get('feelslike_c'),
            "feels_like_f": current.get('feelslike_f'),
            "uv_index": current.get('uv'),
            "last_updated": current.get('last_updated')
        }

        logger.info(f"Weather data retrieved successfully for {location}: {result['temperature']}{unit_symbol}, {result['condition']}")
        return result

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            logger.error(f"Weather API: Location not found: {location}")
            return {
                "success": False,
                "error": f"Location '{location}' not found. Please check the spelling or try a different format."
            }
        logger.error(f"Weather API HTTP error: {e}")
        return {
            "success": False,
            "error": f"Failed to fetch weather data: {str(e)}"
        }
    except requests.exceptions.Timeout:
        logger.error("Weather API request timed out")
        return {
            "success": False,
            "error": "Weather API request timed out. Please try again."
        }
    except Exception as e:
        logger.error(f"Weather API error: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Weather lookup failed: {str(e)}"
        }


# Export required components
__all__ = ['TOOL_DEFINITION', 'execute']
```

#### Step 4: Create Tests

`tests/test_weather_api.py`:
```python
"""Unit tests for weather_api tool."""

import pytest
import os
from unittest.mock import patch, MagicMock
from llf.tools_manager import ToolsManager


class TestWeatherAPI:
    """Test weather_api tool."""

    def setup_method(self):
        """Setup test environment."""
        self.manager = ToolsManager()
        # Import tool if not already in registry
        if not self.manager.get_tool_info('weather_api'):
            self.manager.import_tool('weather_api')
        self.module = self.manager.load_tool_module('weather_api')

    def test_tool_definition_structure(self):
        """Test TOOL_DEFINITION has correct structure."""
        tool_def = self.module.TOOL_DEFINITION

        assert tool_def['type'] == 'function'
        assert tool_def['function']['name'] == 'get_weather'
        assert 'location' in tool_def['function']['parameters']['properties']
        assert 'units' in tool_def['function']['parameters']['properties']
        assert tool_def['function']['parameters']['required'] == ['location']

    def test_execute_missing_api_key(self):
        """Test execute without API key."""
        old_key = os.environ.pop('WEATHER_API_KEY', None)

        try:
            result = self.module.execute({'location': 'London'})

            assert result['success'] is False
            assert 'WEATHER_API_KEY' in result['error']
        finally:
            if old_key:
                os.environ['WEATHER_API_KEY'] = old_key

    def test_execute_missing_location(self):
        """Test execute without location parameter."""
        os.environ['WEATHER_API_KEY'] = 'test-key'

        try:
            result = self.module.execute({})

            assert result['success'] is False
            assert 'required' in result['error'].lower()
        finally:
            os.environ.pop('WEATHER_API_KEY', None)

    def test_execute_success_celsius(self):
        """Test successful weather fetch in celsius."""
        os.environ['WEATHER_API_KEY'] = 'test-key'

        try:
            # Mock requests.get
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'location': {
                    'name': 'London',
                    'region': 'City of London, Greater London',
                    'country': 'United Kingdom'
                },
                'current': {
                    'temp_c': 15.0,
                    'temp_f': 59.0,
                    'condition': {'text': 'Partly cloudy'},
                    'humidity': 72,
                    'wind_kph': 12.5,
                    'wind_mph': 7.8,
                    'feelslike_c': 14.0,
                    'feelslike_f': 57.2,
                    'uv': 3.0,
                    'last_updated': '2024-01-06 14:30'
                }
            }

            with patch('requests.get', return_value=mock_response):
                result = self.module.execute({
                    'location': 'London',
                    'units': 'celsius'
                })

                assert result['success'] is True
                assert result['location'] == 'London'
                assert result['temperature'] == 15.0
                assert result['temperature_display'] == '15.0°C'
                assert result['condition'] == 'Partly cloudy'
                assert result['humidity'] == 72
        finally:
            os.environ.pop('WEATHER_API_KEY', None)

    def test_execute_success_fahrenheit(self):
        """Test successful weather fetch in fahrenheit."""
        os.environ['WEATHER_API_KEY'] = 'test-key'

        try:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                'location': {'name': 'New York', 'region': 'New York', 'country': 'USA'},
                'current': {
                    'temp_c': 20.0,
                    'condition': {'text': 'Sunny'},
                    'humidity': 60,
                    'wind_kph': 10.0,
                    'wind_mph': 6.2,
                    'feelslike_c': 19.0,
                    'feelslike_f': 66.2,
                    'uv': 5.0,
                    'last_updated': '2024-01-06 09:30'
                }
            }

            with patch('requests.get', return_value=mock_response):
                result = self.module.execute({
                    'location': 'New York',
                    'units': 'fahrenheit'
                })

                assert result['success'] is True
                assert result['temperature'] == 68.0  # 20°C = 68°F
                assert result['temperature_display'] == '68.0°F'
        finally:
            os.environ.pop('WEATHER_API_KEY', None)

    def test_execute_location_not_found(self):
        """Test execute with invalid location."""
        os.environ['WEATHER_API_KEY'] = 'test-key'

        try:
            # Mock 400 error response
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.raise_for_status.side_effect = Exception("400 Error")

            with patch('requests.get', return_value=mock_response):
                result = self.module.execute({'location': 'InvalidCityXYZ123'})

                assert result['success'] is False
                assert 'not found' in result['error'].lower()
        finally:
            os.environ.pop('WEATHER_API_KEY', None)

    def test_execute_timeout(self):
        """Test execute with API timeout."""
        os.environ['WEATHER_API_KEY'] = 'test-key'

        try:
            import requests

            with patch('requests.get', side_effect=requests.exceptions.Timeout()):
                result = self.module.execute({'location': 'London'})

                assert result['success'] is False
                assert 'timeout' in result['error'].lower()
        finally:
            os.environ.pop('WEATHER_API_KEY', None)
```

Run tests:
```bash
pytest tests/test_weather_api.py -v --cov=tools.weather_api
```

#### Step 5: Import and Configure

```bash
# Import tool into registry
llf tool import weather_api

# Set API key (get free key from https://www.weatherapi.com)
export WEATHER_API_KEY="your-api-key-here"

# Enable the tool
llf tool enable weather_api

# Verify it's enabled
llf tool info weather_api
```

#### Step 6: Use in Conversation

```bash
llf chat

> User: What's the weather in Tokyo?

> LLM: [Calls: get_weather(location='Tokyo', units='celsius')]

       The weather in Tokyo is currently 18°C and partly cloudy,
       with 65% humidity and light winds at 8 km/h.
```

---

## Tool Security

### Security Model

All tools follow a **whitelist-only, least-privilege** security model:

```
┌─────────────────────────────────────────────────┐
│              Tool Security Layers               │
├─────────────────────────────────────────────────┤
│  1. Tool Enabled Check (disabled by default)    │
│  2. Whitelist Validation (patterns/paths)       │
│  3. Dangerous Operation Detection               │
│  4. Permission Mode Check (ro/rw)               │
│  5. Size/Timeout Limits                         │
│  6. Path Traversal Prevention                   │
│  7. Shell Injection Prevention                  │
│  8. Comprehensive Logging                       │
└─────────────────────────────────────────────────┘
```

### Whitelist Patterns

#### Glob Patterns
```
*.txt                    # All .txt files
*.py                     # All Python files
config/*.json            # JSON files in config/
docs/**/*.md             # Markdown files anywhere under docs/
test_*.py                # Test files
```

#### Fully Qualified Paths
```
/home/user/project/README.md          # Specific file
/var/log/myapp/                       # Specific directory
/home/user/project/src/main.py        # Exact path
```

### Dangerous Paths (`file_access`)

These paths **always require approval**, even if whitelisted:

| Pattern | Description |
|---------|-------------|
| `/etc/*` | System configuration |
| `/sys/*`, `/proc/*` | System files |
| `/dev/*` | Device files |
| `/boot/*` | Boot files |
| `/root/*` | Root user home |
| `~/.ssh/*` | SSH keys |
| `~/.aws/*`, `~/.gcp/*` | Cloud credentials |
| `~/.gnupg/*` | GPG keys |
| `*.key`, `*.pem` | Private keys, certificates |
| `*credentials*`, `*password*` | Credential files |
| `*.env` | Environment files |

### Dangerous Commands (`command_exec`)

These commands **always require approval**, even if whitelisted:

| Command | Risk |
|---------|------|
| `rm` | Delete files |
| `del` | Delete (Windows) |
| `format` | Format disks |
| `mkfs` | Make filesystem |
| `dd` | Disk write (can destroy data) |

### Best Practices

1. **Start Disabled**: All tools disabled by default
2. **Minimal Whitelist**: Only whitelist what's needed
3. **Read-Only First**: Use `ro` mode when possible
4. **Root Directory**: Use `root_dir` to contain file access
5. **Logging**: All operations are logged
6. **Review Logs**: Regularly audit tool usage
7. **API Keys**: Store in environment variables, never in code
8. **Testing**: Test tools in isolation before enabling

---

## Testing Tools

### Unit Testing

```bash
# Test specific tool
pytest tests/test_file_access_comprehensive.py -v

# Test with coverage
pytest tests/test_command_exec_comprehensive.py --cov=tools.command_exec --cov-report=term-missing

# Test all tools
pytest tests/test_*tool* tests/test_*command* tests/test_file* -v
```

### Integration Testing

```bash
# Test tool in actual conversation
llf chat --enable-tool file_access

> User: Read the README file
> LLM: [Uses file_access to read README.md]
```

### Coverage Goals

- **Unit Tests**: 90%+ coverage
- **Integration Tests**: Test with LLM in conversation
- **Error Cases**: Test all failure modes
- **Security**: Test whitelist, dangerous paths/commands

---

## Additional Resources

- **Tool Template**: [TOOL_TEMPLATE.md](./TOOL_TEMPLATE.md) - Detailed template with all fields
- **Security Guide**: Security best practices for tool development
- **API Reference**: Tool function call format and return values
- **Examples**: Study existing tools in this directory

---

## Contributing

To contribute a new tool:

1. Create tool directory with `config.json` and `__init__.py`
2. Follow security best practices
3. Write comprehensive unit tests (90%+ coverage)
4. Document tool usage with examples
5. Submit PR with: code, tests, documentation

---

## Tool Status Summary

| Tool | Status | Security | Coverage | Dependencies |
|------|--------|----------|----------|--------------|
| `command_exec` | ⚠️ Disabled | Whitelist, Dangerous Cmds | 94% | - |
| `file_access` | ⚠️ Disabled | Whitelist, Dangerous Paths | 91% | - |
| `internet_duckduckgo` | Disabled | - | 97% | `ddgs` |
| `internet_google_api` | Disabled | API Key | 72% | `google-api-python-client` |
| `internet_google_webscrape` | Disabled | - | 82% | `googlesearch-python` |
| `xml_format` | ✅ Enabled | - | 100% | - |

---

**Version**: 1.0.0
**Last Updated**: January 6, 2024
**Framework**: Local LLM Framework (LLF)
