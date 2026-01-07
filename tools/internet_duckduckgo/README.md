# Internet Search Tool - DuckDuckGo

Search the internet using DuckDuckGo's free search service.

## Features

- **Free**: No API keys required
- **Privacy-focused**: DuckDuckGo doesn't track searches
- **Reliable**: Established search provider
- **Simple**: Easy to use, returns clean results

## Usage

The LLM can call this tool when it needs to:
- Look up current information
- Research topics
- Find facts or statistics
- Get recent news
- Discover resources or documentation

## Parameters

- `query` (required): The search query string
- `max_results` (optional): Number of results to return (1-20, default: 5)

## Return Format

```json
{
  "success": true,
  "query": "search query",
  "num_results": 5,
  "results": [
    {
      "title": "Result Title",
      "url": "https://example.com",
      "snippet": "Brief description of the result..."
    }
  ]
}
```

## Installation

The tool requires the `ddgs` library:

```bash
pip install ddgs
```

## Configuration

Enable this tool in the tools registry:

```bash
llf tool enable internet_duckduckgo
```

Check status:

```bash
llf tool info internet_duckduckgo
```

## Example Conversation

```
User: What are the latest developments in AI?
Assistant: Let me search for recent AI developments.
[Calls search_internet_duckduckgo with query="latest AI developments 2026"]
Assistant: Based on my search results, here are the latest AI developments...
```

## Security & Privacy

- No authentication required
- No tracking or logging by DuckDuckGo
- Safe for general web searches
- Results are public web content

## Limitations

- Results are limited to public web content
- May be rate-limited by DuckDuckGo
- No control over result quality (depends on DuckDuckGo's algorithm)
- Limited to text-based search results
