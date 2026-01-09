"""
Internet Search Tool - Google Web Scraping

This tool enables the LLM to search Google via web scraping.
It's free, doesn't require API keys, but may have rate limits.
"""

from typing import Dict, Any
from llf.logging_config import get_logger

logger = get_logger(__name__)

# Tool definition for LLM
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_internet_google",
        "description": "Search the internet using Google (via web scraping). Use this when you need to find current information with Google's search results. May have better quality results than DuckDuckGo. Returns a list of search results with titles and URLs.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific and clear about what you're looking for."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (1-20). Defaults to 5.",
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["query"]
        }
    }
}


def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Google search via web scraping.

    Args:
        arguments: Dict with 'query' and optional 'max_results'

    Returns:
        Dict with success status and search results
    """
    try:
        # Import here to avoid dependency issues if not installed
        from googlesearch import search

        query = arguments.get('query')
        max_results = arguments.get('max_results', 5)

        # Validate inputs
        if not query:
            return {
                "success": False,
                "error": "Query parameter is required"
            }

        # Ensure max_results is within bounds
        max_results = max(1, min(20, int(max_results)))

        logger.info(f"Google search: '{query}' (max_results={max_results})")

        # Perform search
        results = []
        try:
            search_results = search(query, num_results=max_results, advanced=True)

            for result in search_results:
                results.append({
                    "title": result.title if hasattr(result, 'title') else 'No title',
                    "url": result.url if hasattr(result, 'url') else str(result),
                    "snippet": result.description if hasattr(result, 'description') else 'No description available'
                })

                # Stop if we've reached max_results
                if len(results) >= max_results:
                    break

        except Exception as search_error:
            logger.warning(f"Google search error (may be rate limited): {search_error}")
            # Try simple search as fallback
            try:
                simple_results = list(search(query, num_results=max_results))
                for url in simple_results[:max_results]:
                    results.append({
                        "title": "Search Result",
                        "url": url,
                        "snippet": "No description available (simple search)"
                    })
            except Exception as fallback_error:
                logger.error(f"Google search fallback also failed: {fallback_error}")
                return {
                    "success": False,
                    "error": f"Search failed - you may be rate limited. Try again in a few minutes. Error: {str(fallback_error)}"
                }

        logger.info(f"Google search returned {len(results)} results")

        return {
            "success": True,
            "query": query,
            "num_results": len(results),
            "results": results
        }

    except ImportError:
        logger.error("googlesearch-python library not installed")
        return {
            "success": False,
            "error": "googlesearch-python library is not installed. Install with: pip install googlesearch-python"
        }
    except Exception as e:
        logger.error(f"Google search failed: {e}")
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }


__all__ = ['TOOL_DEFINITION', 'execute']
