"""
Unit tests for webpage fetcher tool.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from tools.webpage_fetcher import execute, _clean_html_to_text


class TestCleanHtmlToText:
    """Test HTML cleaning functionality."""

    def test_basic_html_cleaning(self):
        """Test basic HTML tag removal."""
        html = "<html><body><p>Hello World</p></body></html>"
        result = _clean_html_to_text(html)
        assert "Hello World" in result
        assert "<p>" not in result
        assert "<html>" not in result

    def test_script_removal(self):
        """Test that script tags are removed."""
        html = """
        <html>
        <head><script>alert('test');</script></head>
        <body>
            <p>Content</p>
            <script>console.log('more');</script>
        </body>
        </html>
        """
        result = _clean_html_to_text(html)
        assert "Content" in result
        assert "alert" not in result
        assert "console.log" not in result
        assert "<script>" not in result

    def test_style_removal(self):
        """Test that style tags are removed."""
        html = """
        <html>
        <head><style>body { color: red; }</style></head>
        <body><p>Content</p></body>
        </html>
        """
        result = _clean_html_to_text(html)
        assert "Content" in result
        assert "color: red" not in result
        assert "<style>" not in result

    def test_whitespace_normalization(self):
        """Test that excessive whitespace is normalized."""
        html = """
        <html>
        <body>
            <p>Line 1</p>



            <p>Line 2</p>
        </body>
        </html>
        """
        result = _clean_html_to_text(html)
        assert "Line 1" in result
        assert "Line 2" in result
        # Should not have more than 2 consecutive newlines
        assert "\n\n\n" not in result


class TestExecute:
    """Test execute function."""

    def test_missing_url_parameter(self):
        """Test error when URL is missing."""
        result = execute({})
        assert result["success"] is False
        assert "URL parameter is required" in result["error"]

    def test_invalid_url_scheme(self):
        """Test error when URL doesn't have http/https scheme."""
        result = execute({"url": "ftp://example.com"})
        assert result["success"] is False
        assert "must start with http" in result["error"]

    def test_invalid_url_format(self):
        """Test error when URL format is invalid."""
        result = execute({"url": "http://"})
        assert result["success"] is False
        assert "Invalid URL" in result["error"]

    @patch('requests.get')
    def test_successful_fetch(self, mock_get):
        """Test successful webpage fetch."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Test Page</h1><p>Content here</p></body></html>"
        mock_response.url = "https://example.com"
        mock_response.headers = {'content-type': 'text/html'}
        mock_get.return_value = mock_response

        result = execute({"url": "https://example.com"})

        assert result["success"] is True
        assert "Test Page" in result["content"]
        assert "Content here" in result["content"]
        assert result["url"] == "https://example.com"
        assert mock_get.called

    @patch('requests.get')
    def test_timeout_error(self, mock_get):
        """Test timeout handling."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        result = execute({"url": "https://example.com"})

        assert result["success"] is False
        assert "timed out" in result["error"].lower()

    @patch('requests.get')
    def test_connection_error(self, mock_get):
        """Test connection error handling."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()

        result = execute({"url": "https://example.com"})

        assert result["success"] is False
        assert "connect" in result["error"].lower()

    @patch('requests.get')
    def test_http_error(self, mock_get):
        """Test HTTP error handling (404, 500, etc.)."""
        import requests
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_get.return_value = mock_response

        result = execute({"url": "https://example.com/notfound"})

        assert result["success"] is False
        assert "HTTP error" in result["error"] or "404" in str(result["error"])

    @patch('requests.get')
    def test_unsupported_content_type(self, mock_get):
        """Test error when content type is not HTML or text."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'application/pdf'}
        mock_get.return_value = mock_response

        result = execute({"url": "https://example.com/file.pdf"})

        assert result["success"] is False
        assert "Unsupported content type" in result["error"]

    @patch('requests.get')
    def test_content_truncation(self, mock_get):
        """Test that long content is truncated."""
        # Create content longer than max_length
        long_content = "<html><body>" + ("x" * 20000) + "</body></html>"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = long_content
        mock_response.url = "https://example.com"
        mock_response.headers = {'content-type': 'text/html'}
        mock_get.return_value = mock_response

        result = execute({"url": "https://example.com", "max_length": 5000})

        assert result["success"] is True
        assert result["content_length"] <= 5100  # Some buffer for truncation message
        assert "truncated" in result["content"].lower()

    @patch('requests.get')
    def test_max_length_bounds(self, mock_get):
        """Test that max_length is clamped to valid range."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.url = "https://example.com"
        mock_response.headers = {'content-type': 'text/html'}
        mock_get.return_value = mock_response

        # Test value too low
        result = execute({"url": "https://example.com", "max_length": 100})
        assert result["success"] is True  # Should clamp to minimum (1000)

        # Test value too high
        result = execute({"url": "https://example.com", "max_length": 100000})
        assert result["success"] is True  # Should clamp to maximum (50000)

    @patch('requests.get')
    def test_redirect_handling(self, mock_get):
        """Test that redirects are followed and final URL is returned."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Final page</body></html>"
        mock_response.url = "https://example.com/final"  # Different from requested
        mock_response.headers = {'content-type': 'text/html'}
        mock_get.return_value = mock_response

        result = execute({"url": "https://example.com/redirect"})

        assert result["success"] is True
        assert result["url"] == "https://example.com/redirect"  # Original URL
        assert result["final_url"] == "https://example.com/final"  # After redirect

    @patch('requests.get')
    def test_user_agent_set(self, mock_get):
        """Test that User-Agent header is set."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.url = "https://example.com"
        mock_response.headers = {'content-type': 'text/html'}
        mock_get.return_value = mock_response

        execute({"url": "https://example.com"})

        # Check that get was called with headers
        call_args = mock_get.call_args
        assert 'headers' in call_args.kwargs
        assert 'User-Agent' in call_args.kwargs['headers']


class TestToolDefinition:
    """Test tool definition structure."""

    def test_tool_definition_exists(self):
        """Test that TOOL_DEFINITION is properly defined."""
        from tools.webpage_fetcher import TOOL_DEFINITION

        assert TOOL_DEFINITION is not None
        assert TOOL_DEFINITION["type"] == "function"
        assert "function" in TOOL_DEFINITION

    def test_function_name(self):
        """Test that function name is correct."""
        from tools.webpage_fetcher import TOOL_DEFINITION

        assert TOOL_DEFINITION["function"]["name"] == "fetch_webpage"

    def test_required_parameters(self):
        """Test that URL is a required parameter."""
        from tools.webpage_fetcher import TOOL_DEFINITION

        params = TOOL_DEFINITION["function"]["parameters"]
        assert "url" in params["required"]
        assert "url" in params["properties"]

    def test_optional_parameters(self):
        """Test that max_length is optional."""
        from tools.webpage_fetcher import TOOL_DEFINITION

        params = TOOL_DEFINITION["function"]["parameters"]
        assert "max_length" in params["properties"]
        assert "max_length" not in params["required"]
