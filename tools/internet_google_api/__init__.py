"""
Internet Search Tool - Google Custom Search API

This tool enables the LLM to search the internet using Google's Custom Search API.
Requires API key and Custom Search Engine ID. Paid after free tier (100 queries/day).
"""

import os
from typing import Dict, Any
from llf.logging_config import get_logger

logger = get_logger(__name__)

# Tool definition for LLM
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_internet_google_api",
        "description": "Search the internet using Google's Custom Search API (high quality results, requires API key). Use this when you need reliable, high-quality search results from Google. Note: Limited to 100 free queries per day, then $5 per 1000 queries.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific and clear about what you're looking for."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (1-10). Defaults to 5.",
                    "minimum": 1,
                    "maximum": 10
                }
            },
            "required": ["query"]
        }
    }
}


def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Google Custom Search API search.

    Args:
        arguments: Dict with 'query' and optional 'max_results'

    Returns:
        Dict with success status and search results
    """
    try:
        # Import here to avoid dependency issues if not installed
        from googleapiclient.discovery import build

        query = arguments.get('query')
        max_results = arguments.get('max_results', 5)

        # Validate inputs
        if not query:
            return {
                "success": False,
                "error": "Query parameter is required"
            }

        # Ensure max_results is within bounds (API limit is 10 per request)
        max_results = max(1, min(10, int(max_results)))

        # Get API credentials from environment variables
        api_key = os.environ.get('GOOGLE_API_KEY')
        cse_id = os.environ.get('GOOGLE_CSE_ID')

        if not api_key:
            return {
                "success": False,
                "error": "GOOGLE_API_KEY environment variable not set. Get an API key from https://console.cloud.google.com/"
            }

        if not cse_id:
            return {
                "success": False,
                "error": "GOOGLE_CSE_ID environment variable not set. Create a Custom Search Engine at https://cse.google.com/"
            }

        logger.info(f"Google API search: '{query}' (max_results={max_results})")

        # Build the Custom Search service
        service = build("customsearch", "v1", developerKey=api_key)

        # Perform search
        results = []
        try:
            response = service.cse().list(
                q=query,
                cx=cse_id,
                num=max_results
            ).execute()

            # Extract results
            if 'items' in response:
                for item in response['items']:
                    results.append({
                        "title": item.get('title', 'No title'),
                        "url": item.get('link', ''),
                        "snippet": item.get('snippet', 'No description available')
                    })

            logger.info(f"Google API search returned {len(results)} results")

        except Exception as api_error:
            error_msg = str(api_error)
            logger.error(f"Google API search error: {error_msg}")

            # Check for common errors
            if 'quota' in error_msg.lower():
                return {
                    "success": False,
                    "error": "Daily quota exceeded. You have 100 free queries per day. After that, it costs $5 per 1000 queries."
                }
            elif 'invalid' in error_msg.lower() and 'key' in error_msg.lower():
                return {
                    "success": False,
                    "error": "Invalid API key. Check your GOOGLE_API_KEY environment variable."
                }
            elif 'invalid' in error_msg.lower() and ('cx' in error_msg.lower() or 'cse' in error_msg.lower()):
                return {
                    "success": False,
                    "error": "Invalid Custom Search Engine ID. Check your GOOGLE_CSE_ID environment variable."
                }
            else:
                return {
                    "success": False,
                    "error": f"Google API error: {error_msg}"
                }

        return {
            "success": True,
            "query": query,
            "num_results": len(results),
            "results": results
        }

    except ImportError:
        logger.error("google-api-python-client library not installed")
        return {
            "success": False,
            "error": "google-api-python-client library is not installed. Install with: pip install google-api-python-client"
        }
    except Exception as e:
        logger.error(f"Google API search failed: {e}")
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }


__all__ = ['TOOL_DEFINITION', 'execute']
