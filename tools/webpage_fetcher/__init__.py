"""
Webpage Fetcher Tool - Fetch and extract clean text content from web pages.

This tool enables the LLM to retrieve and read content from web URLs.
It fetches HTML, converts it to clean readable text, and extracts main content.
"""

from typing import Dict, Any
from llf.logging_config import get_logger
import re

logger = get_logger(__name__)

# Tool definition for LLM
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "fetch_webpage",
        "description": "Fetch and read the content of any web page from a URL. When you see a URL starting with http:// or https://, use this tool to retrieve and read its content. Returns clean, readable text extracted from the HTML page. Works with any website, documentation, articles, repositories, or web resources.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL of the webpage to fetch (must start with http:// or https://)"
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum number of characters to return (1000-50000). Defaults to 10000. Use smaller values for quick info, larger for detailed content.",
                    "minimum": 1000,
                    "maximum": 50000
                }
            },
            "required": ["url"]
        }
    }
}


def _clean_html_to_text(html: str) -> str:
    """
    Convert HTML to clean readable text.

    Args:
        html: Raw HTML content

    Returns:
        Clean text with formatting preserved
    """
    try:
        from bs4 import BeautifulSoup

        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script, style, and other non-content elements
        for element in soup(['script', 'style', 'meta', 'link', 'noscript', 'iframe']):
            element.decompose()

        # Try to extract main content (common patterns)
        main_content = None
        for selector in ['main', 'article', '[role="main"]', '.main-content', '#main-content', '.content']:
            main_content = soup.select_one(selector)
            if main_content:
                break

        # Use main content if found, otherwise use body
        content = main_content if main_content else soup.body
        if not content:
            content = soup

        # Get text
        text = content.get_text(separator='\n', strip=True)

        # Clean up excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple blank lines to double
        text = re.sub(r' +', ' ', text)  # Multiple spaces to single
        text = text.strip()

        return text

    except ImportError:
        # Fallback: simple regex-based HTML stripping
        logger.warning("BeautifulSoup not available, using basic HTML stripping")
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()


def execute(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute webpage fetch operation.

    Args:
        arguments: Dict with 'url' and optional 'max_length'

    Returns:
        Dict with success status and webpage content
    """
    try:
        import requests
        from urllib.parse import urlparse

        url = arguments.get('url')
        max_length = arguments.get('max_length', 10000)

        # Validate URL
        if not url:
            return {
                "success": False,
                "error": "URL parameter is required"
            }

        # Ensure URL has scheme
        if not url.startswith(('http://', 'https://')):
            return {
                "success": False,
                "error": "URL must start with http:// or https://"
            }

        # Validate URL format
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return {
                    "success": False,
                    "error": "Invalid URL format"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Invalid URL: {str(e)}"
            }

        # Ensure max_length is within bounds
        max_length = max(1000, min(50000, int(max_length)))

        logger.info(f"Fetching webpage: {url} (max_length={max_length})")

        # Set timeout and user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Fetch the page
        try:
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timed out after 10 seconds"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Failed to connect to the URL"
            }
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "error": f"HTTP error {response.status_code}: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch URL: {str(e)}"
            }

        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if 'text/html' not in content_type and 'text/plain' not in content_type:
            return {
                "success": False,
                "error": f"Unsupported content type: {content_type}. Only HTML and plain text are supported."
            }

        # Get content
        html_content = response.text

        # Convert to clean text
        text_content = _clean_html_to_text(html_content)

        # Truncate if needed
        if len(text_content) > max_length:
            text_content = text_content[:max_length] + f"\n\n[Content truncated at {max_length} characters. Original page was {len(text_content)} characters.]"

        logger.info(f"Successfully fetched webpage: {url} ({len(text_content)} characters)")

        return {
            "success": True,
            "url": url,
            "final_url": response.url,  # In case of redirects
            "content_length": len(text_content),
            "content": text_content,
            "was_truncated": len(response.text) > max_length
        }

    except ImportError as e:
        logger.error(f"Required library not installed: {e}")
        if 'requests' in str(e):
            return {
                "success": False,
                "error": "requests library is not installed. Install with: pip install requests"
            }
        elif 'bs4' in str(e) or 'beautifulsoup' in str(e).lower():
            return {
                "success": False,
                "error": "beautifulsoup4 library is not installed. Install with: pip install beautifulsoup4"
            }
        else:
            return {
                "success": False,
                "error": f"Missing required library: {str(e)}"
            }
    except Exception as e:
        logger.error(f"Webpage fetch failed: {e}")
        return {
            "success": False,
            "error": f"Failed to fetch webpage: {str(e)}"
        }


__all__ = ['TOOL_DEFINITION', 'execute']
