"""
Execute function for DuckDuckGo internet search tool.
"""

from typing import Dict, Any
from llf.logging_config import get_logger

logger = get_logger(__name__)


def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute DuckDuckGo search.

    Args:
        arguments: Dict with 'query' and optional 'max_results'

    Returns:
        Dict with success status and search results
    """
    try:
        # Import here to avoid dependency issues if not installed
        try:
            from ddgs import DDGS
        except ImportError:
            # Fallback to old package name for backwards compatibility
            from duckduckgo_search import DDGS

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

        logger.info(f"DuckDuckGo search: '{query}' (max_results={max_results})")

        # Perform search
        results = []
        with DDGS() as ddgs:
            search_results = ddgs.text(query, max_results=max_results)

            for result in search_results:
                results.append({
                    "title": result.get('title', 'No title'),
                    "url": result.get('href', ''),
                    "snippet": result.get('body', 'No description available')
                })

        logger.info(f"DuckDuckGo search returned {len(results)} results")

        return {
            "success": True,
            "query": query,
            "num_results": len(results),
            "results": results
        }

    except ImportError:
        logger.error("ddgs library not installed")
        return {
            "success": False,
            "error": "ddgs library is not installed. Install with: pip install ddgs"
        }
    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")
        return {
            "success": False,
            "error": f"Search failed: {str(e)}"
        }
