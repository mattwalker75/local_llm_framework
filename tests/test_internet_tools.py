"""
Unit tests for Internet Search Tools.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from llf.tools_manager import ToolsManager

# Check if optional dependencies are installed
try:
    import ddgs
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

try:
    import googlesearch
    GOOGLESEARCH_AVAILABLE = True
except ImportError:
    GOOGLESEARCH_AVAILABLE = False

try:
    from googleapiclient import discovery
    GOOGLEAPI_AVAILABLE = True
except ImportError:
    GOOGLEAPI_AVAILABLE = False


class TestInternetDuckDuckGo:
    """Test search_internet_duckduckgo tool."""

    def test_load_tool_module(self):
        """Test loading the duckduckgo tool module."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_duckduckgo')

        assert module is not None
        assert hasattr(module, 'TOOL_DEFINITION')
        assert hasattr(module, 'execute')

    def test_tool_definition_structure(self):
        """Test that TOOL_DEFINITION has correct structure."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_duckduckgo')

        tool_def = module.TOOL_DEFINITION
        assert tool_def['type'] == 'function'
        assert 'function' in tool_def
        assert tool_def['function']['name'] == 'search_internet_duckduckgo'
        assert 'parameters' in tool_def['function']
        assert 'query' in tool_def['function']['parameters']['properties']

    @pytest.mark.skipif(not DDGS_AVAILABLE, reason="ddgs library not installed")
    def test_execute_missing_query(self):
        """Test execute with missing query parameter."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_duckduckgo')

        result = module.execute({})
        assert result['success'] is False
        assert 'required' in result['error'].lower()

    @pytest.mark.skipif(not DDGS_AVAILABLE, reason="ddgs library not installed")
    def test_execute_with_valid_query(self):
        """Test execute with valid query (mocked)."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_duckduckgo')

        # Mock the DDGS class
        mock_result = {
            'title': 'Test Result',
            'href': 'https://example.com',
            'body': 'Test description'
        }

        with patch('ddgs.DDGS') as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_instance.text = Mock(return_value=[mock_result])
            mock_ddgs.return_value = mock_instance

            result = module.execute({'query': 'test query', 'max_results': 1})

            assert result['success'] is True
            assert result['query'] == 'test query'
            assert result['num_results'] == 1
            assert len(result['results']) == 1
            assert result['results'][0]['title'] == 'Test Result'
            assert result['results'][0]['url'] == 'https://example.com'

    @pytest.mark.skipif(not DDGS_AVAILABLE, reason="ddgs library not installed")
    def test_execute_max_results_bounds(self):
        """Test that max_results is bounded between 1 and 20."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_duckduckgo')

        with patch('ddgs.DDGS') as mock_ddgs:
            mock_instance = MagicMock()
            mock_instance.__enter__ = Mock(return_value=mock_instance)
            mock_instance.__exit__ = Mock(return_value=False)
            mock_instance.text = Mock(return_value=[])
            mock_ddgs.return_value = mock_instance

            # Test upper bound
            result = module.execute({'query': 'test', 'max_results': 100})
            assert result['success'] is True
            # Should have been capped at 20
            call_args = mock_instance.text.call_args
            assert call_args[1]['max_results'] <= 20

            # Test lower bound
            result = module.execute({'query': 'test', 'max_results': 0})
            assert result['success'] is True
            call_args = mock_instance.text.call_args
            assert call_args[1]['max_results'] >= 1


class TestInternetGoogleWebscrape:
    """Test search_internet_google tool."""

    def test_load_tool_module(self):
        """Test loading the google webscrape tool module."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_google')

        assert module is not None
        assert hasattr(module, 'TOOL_DEFINITION')
        assert hasattr(module, 'execute')

    def test_tool_definition_structure(self):
        """Test that TOOL_DEFINITION has correct structure."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_google')

        tool_def = module.TOOL_DEFINITION
        assert tool_def['type'] == 'function'
        assert 'function' in tool_def
        assert tool_def['function']['name'] == 'search_internet_google'
        assert 'parameters' in tool_def['function']
        assert 'query' in tool_def['function']['parameters']['properties']

    @pytest.mark.skipif(not GOOGLESEARCH_AVAILABLE, reason="googlesearch library not installed")
    def test_execute_missing_query(self):
        """Test execute with missing query parameter."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_google')

        result = module.execute({})
        assert result['success'] is False
        assert 'required' in result['error'].lower()

    @pytest.mark.skipif(not GOOGLESEARCH_AVAILABLE, reason="googlesearch library not installed")
    def test_execute_with_valid_query(self):
        """Test execute with valid query (mocked)."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_google')

        # Mock the search function
        mock_result = MagicMock()
        mock_result.title = 'Test Result'
        mock_result.url = 'https://example.com'
        mock_result.description = 'Test description'

        with patch('googlesearch.search') as mock_search:
            mock_search.return_value = [mock_result]

            result = module.execute({'query': 'test query', 'max_results': 1})

            assert result['success'] is True
            assert result['query'] == 'test query'
            assert result['num_results'] == 1
            assert len(result['results']) == 1
            assert result['results'][0]['title'] == 'Test Result'
            assert result['results'][0]['url'] == 'https://example.com'

    @pytest.mark.skipif(not GOOGLESEARCH_AVAILABLE, reason="googlesearch library not installed")
    def test_execute_max_results_bounds(self):
        """Test that max_results is bounded between 1 and 20."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_google')

        with patch('googlesearch.search') as mock_search:
            mock_search.return_value = []

            # Test upper bound
            result = module.execute({'query': 'test', 'max_results': 100})
            assert result['success'] is True

            # Test lower bound
            result = module.execute({'query': 'test', 'max_results': 0})
            assert result['success'] is True


class TestInternetGoogleAPI:
    """Test search_internet_google_api tool."""

    def test_load_tool_module(self):
        """Test loading the google API tool module."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_google_api')

        assert module is not None
        assert hasattr(module, 'TOOL_DEFINITION')
        assert hasattr(module, 'execute')

    def test_tool_definition_structure(self):
        """Test that TOOL_DEFINITION has correct structure."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_google_api')

        tool_def = module.TOOL_DEFINITION
        assert tool_def['type'] == 'function'
        assert 'function' in tool_def
        assert tool_def['function']['name'] == 'search_internet_google_api'
        assert 'parameters' in tool_def['function']
        assert 'query' in tool_def['function']['parameters']['properties']

    @pytest.mark.skipif(not GOOGLEAPI_AVAILABLE, reason="google-api-python-client library not installed")
    def test_execute_missing_query(self):
        """Test execute with missing query parameter."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_google_api')

        result = module.execute({})
        assert result['success'] is False
        assert 'required' in result['error'].lower()

    @pytest.mark.skipif(not GOOGLEAPI_AVAILABLE, reason="google-api-python-client library not installed")
    def test_execute_missing_api_key(self):
        """Test execute with missing API key."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_google_api')

        # Clear environment variables
        import os
        old_api_key = os.environ.pop('GOOGLE_API_KEY', None)
        old_cse_id = os.environ.pop('GOOGLE_CSE_ID', None)

        try:
            result = module.execute({'query': 'test query'})
            assert result['success'] is False
            assert 'GOOGLE_API_KEY' in result['error']
        finally:
            # Restore environment variables
            if old_api_key:
                os.environ['GOOGLE_API_KEY'] = old_api_key
            if old_cse_id:
                os.environ['GOOGLE_CSE_ID'] = old_cse_id

    @pytest.mark.skipif(not GOOGLEAPI_AVAILABLE, reason="google-api-python-client library not installed")
    def test_execute_with_valid_credentials(self):
        """Test execute with valid credentials (mocked)."""
        manager = ToolsManager()
        module = manager.load_tool_module('search_internet_google_api')

        import os
        os.environ['GOOGLE_API_KEY'] = 'test-key'
        os.environ['GOOGLE_CSE_ID'] = 'test-cse-id'

        try:
            with patch('googleapiclient.discovery.build') as mock_build:
                # Mock the API response
                mock_service = MagicMock()
                mock_cse = MagicMock()
                mock_list = MagicMock()

                mock_response = {
                    'items': [{
                        'title': 'Test Result',
                        'link': 'https://example.com',
                        'snippet': 'Test description'
                    }]
                }

                mock_list.execute.return_value = mock_response
                mock_cse.list.return_value = mock_list
                mock_service.cse.return_value = mock_cse
                mock_build.return_value = mock_service

                result = module.execute({'query': 'test query', 'max_results': 1})

                assert result['success'] is True
                assert result['query'] == 'test query'
                assert result['num_results'] == 1
                assert result['results'][0]['title'] == 'Test Result'
        finally:
            os.environ.pop('GOOGLE_API_KEY', None)
            os.environ.pop('GOOGLE_CSE_ID', None)


class TestToolsRegistry:
    """Test that internet tools are properly registered."""

    def test_internet_tools_in_registry(self):
        """Test that internet tools are registered."""
        manager = ToolsManager()

        # Check duckduckgo
        ddg_info = manager.get_tool_info('search_internet_duckduckgo')
        assert ddg_info is not None
        assert ddg_info['type'] == 'llm_invokable'
        assert ddg_info['directory'] == 'internet_duckduckgo'

        # Check google webscrape
        google_info = manager.get_tool_info('search_internet_google')
        assert google_info is not None
        assert google_info['type'] == 'llm_invokable'
        assert google_info['directory'] == 'internet_google_webscrape'

        # Check google API
        google_api_info = manager.get_tool_info('search_internet_google_api')
        assert google_api_info is not None
        assert google_api_info['type'] == 'llm_invokable'
        assert google_api_info['directory'] == 'internet_google_api'

    def test_get_enabled_llm_invokable_tools_when_disabled(self):
        """Test that disabled internet tools don't appear in enabled list."""
        manager = ToolsManager()

        # Temporarily disable the tools by directly modifying the registry
        original_states = {}

        for tool_name in ['search_internet_duckduckgo', 'search_internet_google', 'search_internet_google_api']:
            tool = manager.get_tool_info(tool_name)
            if tool:
                original_states[tool_name] = tool.get('enabled', True)
                tool['enabled'] = False

        enabled_tools = manager.get_enabled_llm_invokable_tools()

        tool_names = [t['name'] for t in enabled_tools]
        assert 'search_internet_duckduckgo' not in tool_names
        assert 'search_internet_google' not in tool_names
        assert 'search_internet_google_api' not in tool_names

        # Restore original states
        for tool_name, state in original_states.items():
            tool = manager.get_tool_info(tool_name)
            if tool:
                tool['enabled'] = state

    def test_enable_internet_tool(self, tmp_path):
        """Test enabling an internet tool."""
        import json

        registry_path = tmp_path / "tools_registry.json"
        registry_path.write_text(json.dumps({
            "version": "1.1",
            "tools": [
                {
                    "name": "internet_duckduckgo",
                    "type": "llm_invokable",
                    "enabled": False,
                    "directory": "internet_duckduckgo"
                }
            ]
        }))

        manager = ToolsManager(registry_path=registry_path)

        # Initially disabled
        assert manager.is_feature_enabled('internet_duckduckgo') is False

        # Enable it
        success = manager.enable_feature('internet_duckduckgo', session_only=False)
        assert success is True
        assert manager.is_feature_enabled('internet_duckduckgo') is True

        # Check it appears in enabled tools
        enabled_tools = manager.get_enabled_llm_invokable_tools()
        tool_names = [t['name'] for t in enabled_tools]
        assert 'internet_duckduckgo' in tool_names
