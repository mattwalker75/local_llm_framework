# Internet Search Tool - Google Custom Search API

Search the internet using Google's official Custom Search API.

## Features

- **High Quality**: Official Google search results
- **Reliable**: Stable API, not affected by HTML changes
- **Structured**: Clean, consistent result format
- **Professional**: Production-ready for applications

## Requirements

### API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the "Custom Search API"
4. Create credentials → API key
5. Set environment variable: `export GOOGLE_API_KEY="your-api-key"`

### Custom Search Engine ID

1. Go to [Programmable Search Engine](https://cse.google.com/)
2. Click "Add" to create a new search engine
3. Configure:
   - Sites to search: Leave empty to search entire web
   - Name: Give it a name
   - Search settings: "Search the entire web"
4. Copy the Search Engine ID
5. Set environment variable: `export GOOGLE_CSE_ID="your-cse-id"`

## Pricing

- **Free Tier**: 100 queries per day
- **Paid**: $5 per 1,000 queries (billed monthly)
- First 100 queries each day are free

## Usage

The LLM can call this tool when it needs:
- High-quality Google search results
- Reliable search (not web scraping)
- Production-level search capability

## Parameters

- `query` (required): The search query string
- `max_results` (optional): Number of results to return (1-10, default: 5)

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

The tool requires the `google-api-python-client` library:

```bash
pip install google-api-python-client
```

## Configuration

### Set Environment Variables

```bash
# In your shell profile (~/.bashrc, ~/.zshrc, etc.)
export GOOGLE_API_KEY="your-api-key-here"
export GOOGLE_CSE_ID="your-custom-search-engine-id"
```

Or set them temporarily:

```bash
# For current session only
export GOOGLE_API_KEY="your-api-key-here"
export GOOGLE_CSE_ID="your-custom-search-engine-id"

# Then run your LLM
source llf_venv/bin/activate
bin/llf chat
```

### Enable the Tool

```bash
llf tool enable internet_google_api
llf tool info internet_google_api
```

## Example Conversation

```
User: Search Google for the latest Python news
Assistant: Let me search for the latest Python news.
[Calls search_internet_google_api with query="latest Python news 2026"]
Assistant: Here are the latest Python news articles from Google...
```

## Error Messages

### Missing API Key
```
GOOGLE_API_KEY environment variable not set.
Get an API key from https://console.cloud.google.com/
```

**Solution**: Set the `GOOGLE_API_KEY` environment variable.

### Missing CSE ID
```
GOOGLE_CSE_ID environment variable not set.
Create a Custom Search Engine at https://cse.google.com/
```

**Solution**: Set the `GOOGLE_CSE_ID` environment variable.

### Quota Exceeded
```
Daily quota exceeded. You have 100 free queries per day.
After that, it costs $5 per 1000 queries.
```

**Solution**:
- Wait until tomorrow for free quota to reset
- Or enable billing in Google Cloud Console
- Or use `internet_duckduckgo` as free alternative

### Invalid API Key
```
Invalid API key. Check your GOOGLE_API_KEY environment variable.
```

**Solution**: Verify your API key is correct and the Custom Search API is enabled.

## Security & Privacy

- Requires valid Google Cloud credentials
- Searches are logged by Google
- Not anonymous
- API key should be kept secure
- Results are public web content

## Advantages vs Free Tools

### vs DuckDuckGo
- ✅ Higher quality results (Google's algorithm)
- ✅ More reliable (official API)
- ✅ Structured data
- ❌ Requires API key
- ❌ Costs money after 100 queries/day

### vs Google Web Scraping
- ✅ No rate limiting
- ✅ More reliable (won't break with HTML changes)
- ✅ Official, supported
- ❌ Requires API key
- ❌ Costs money after 100 queries/day

## Limitations

- **Cost**: $5 per 1,000 queries after free tier
- **Quota**: 100 free queries per day
- **API Limits**: Maximum 10 results per request
- **Setup Required**: Need API key and CSE ID
- **Billing**: Must enable billing for paid usage

## Alternatives

If you don't want to set up API keys or pay:
- Use `internet_duckduckgo` - Free, reliable, no setup
- Use `internet_google_webscrape` - Free Google search (may be rate limited)

## Cost Estimation

- Light usage (< 100 queries/day): **FREE**
- Medium usage (500 queries/day): **$60/month**
- Heavy usage (2000 queries/day): **$285/month**

The first 100 queries each day are always free.
