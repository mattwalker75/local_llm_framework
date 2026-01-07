# Internet Search Tool - Google Web Scraping

Search the internet using Google via web scraping.

## Features

- **Free**: No API keys required
- **Google Results**: Access to Google's search algorithm
- **Established**: Uses proven web scraping techniques

## Usage

The LLM can call this tool when it needs to:
- Search with Google's algorithm for potentially better results
- Find current information
- Research topics
- Get specific facts or resources

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

The tool requires the `googlesearch-python` library:

```bash
pip install googlesearch-python
```

## Configuration

Enable this tool in the tools registry:

```bash
llf tool enable internet_google_webscrape
```

Check status:

```bash
llf tool info internet_google_webscrape
```

## Example Conversation

```
User: Search Google for Python tutorials
Assistant: Let me search Google for Python tutorials.
[Calls search_internet_google with query="Python tutorials"]
Assistant: Here are the top Python tutorials I found on Google...
```

## Important Notes

### Rate Limiting

- **Google may rate limit or block repeated requests**
- If you get errors, wait a few minutes before trying again
- Consider using DuckDuckGo search as an alternative if rate limited
- The tool includes a fallback mechanism for simple searches

### Reliability

- Web scraping can be fragile and may break if Google changes their HTML structure
- Results depend on Google's current page structure
- May not work in all regions or networks

## Security & Privacy

- No authentication required
- Searches are sent to Google (not private)
- May be logged by Google
- Safe for general web searches
- Results are public web content

## Limitations

- **Rate limiting**: Google may block repeated requests
- **Fragile**: Web scraping can break if Google updates their page structure
- **No advanced features**: Limited to basic text search
- **Regional differences**: Results may vary by location

## Alternatives

If this tool is rate limited or not working:
- Use `internet_duckduckgo` tool for reliable free search
- Use `internet_google_api` tool (requires API key, paid after free tier)
