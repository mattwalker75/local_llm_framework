"""
Comprehensive unit tests for Internet Search Tools to improve coverage.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
import sys


class TestInternetDuckDuckGoCoverage:
    """Test error cases and missing paths in internet_duckduckgo."""

    def test_execute_with_mocked_ddgs(self):
        """Test successful search with mocked DDGS."""
        # Mock the DDGS module before import
        mock_ddgs_module = MagicMock()
        mock_ddgs_class = MagicMock()
        mock_instance = MagicMock()

        # Setup context manager
        mock_instance.__enter__ = Mock(return_value=mock_instance)
        mock_instance.__exit__ = Mock(return_value=False)

        # Mock search results
        mock_instance.text.return_value = [
            {
                'title': 'Test Result 1',
                'href': 'https://example.com/1',
                'body': 'Test description 1'
            },
            {
                'title': 'Test Result 2',
                'href': 'https://example.com/2',
                'body': 'Test description 2'
            }
        ]

        mock_ddgs_class.return_value = mock_instance
        mock_ddgs_module.DDGS = mock_ddgs_class

        # Patch sys.modules to make ddgs import work
        with patch.dict('sys.modules', {'ddgs': mock_ddgs_module}):
            from tools.internet_duckduckgo import execute

            result = execute({'query': 'test query', 'max_results': 5})

            assert result['success'] is True
            assert result['query'] == 'test query'
            assert result['num_results'] == 2
            assert len(result['results']) == 2
            assert result['results'][0]['title'] == 'Test Result 1'
            assert result['results'][0]['url'] == 'https://example.com/1'

    def test_execute_max_results_clamping(self):
        """Test that max_results is clamped to valid range."""
        mock_ddgs_module = MagicMock()
        mock_ddgs_class = MagicMock()
        mock_instance = MagicMock()

        mock_instance.__enter__ = Mock(return_value=mock_instance)
        mock_instance.__exit__ = Mock(return_value=False)
        mock_instance.text.return_value = []

        mock_ddgs_class.return_value = mock_instance
        mock_ddgs_module.DDGS = mock_ddgs_class

        with patch.dict('sys.modules', {'ddgs': mock_ddgs_module}):
            from tools.internet_duckduckgo import execute

            # Test upper bound (should be clamped to 20)
            result = execute({'query': 'test', 'max_results': 100})
            assert result['success'] is True
            call_args = mock_instance.text.call_args
            assert call_args[1]['max_results'] == 20

            # Test lower bound (should be clamped to 1)
            result = execute({'query': 'test', 'max_results': 0})
            assert result['success'] is True
            call_args = mock_instance.text.call_args
            assert call_args[1]['max_results'] == 1

    def test_execute_search_exception(self):
        """Test handling of search exceptions."""
        mock_ddgs_module = MagicMock()
        mock_ddgs_class = MagicMock()
        mock_instance = MagicMock()

        mock_instance.__enter__ = Mock(return_value=mock_instance)
        mock_instance.__exit__ = Mock(return_value=False)
        mock_instance.text.side_effect = Exception("API error")

        mock_ddgs_class.return_value = mock_instance
        mock_ddgs_module.DDGS = mock_ddgs_class

        with patch.dict('sys.modules', {'ddgs': mock_ddgs_module}):
            from tools.internet_duckduckgo import execute

            result = execute({'query': 'test'})

            assert result['success'] is False
            assert 'Search failed' in result['error']


class TestInternetGoogleWebscrapeCoverage:
    """Test error cases and missing paths in internet_google_webscrape."""

    def test_execute_with_mocked_search(self):
        """Test successful search with mocked googlesearch."""
        mock_googlesearch = MagicMock()

        # Create mock search result objects with attributes
        mock_result1 = MagicMock()
        mock_result1.title = 'Test Result 1'
        mock_result1.url = 'https://example.com/1'
        mock_result1.description = 'Test description 1'

        mock_result2 = MagicMock()
        mock_result2.title = 'Test Result 2'
        mock_result2.url = 'https://example.com/2'
        mock_result2.description = 'Test description 2'

        mock_googlesearch.search.return_value = [mock_result1, mock_result2]

        with patch.dict('sys.modules', {'googlesearch': mock_googlesearch}):
            from tools.internet_google_webscrape import execute

            result = execute({'query': 'test query', 'max_results': 5})

            assert result['success'] is True
            assert result['query'] == 'test query'
            assert result['num_results'] == 2
            assert len(result['results']) == 2
            assert result['results'][0]['title'] == 'Test Result 1'

    def test_execute_max_results_clamping(self):
        """Test that max_results is clamped to valid range."""
        mock_googlesearch = MagicMock()
        mock_googlesearch.search.return_value = []

        with patch.dict('sys.modules', {'googlesearch': mock_googlesearch}):
            from tools.internet_google_webscrape import execute

            # Test upper bound
            result = execute({'query': 'test', 'max_results': 100})
            assert result['success'] is True
            call_args = mock_googlesearch.search.call_args
            assert call_args[1]['num_results'] == 20

            # Test lower bound
            result = execute({'query': 'test', 'max_results': 0})
            assert result['success'] is True
            call_args = mock_googlesearch.search.call_args
            assert call_args[1]['num_results'] == 1

    def test_execute_search_exception(self):
        """Test handling of search exceptions."""
        mock_googlesearch = MagicMock()
        mock_googlesearch.search.side_effect = Exception("Network error")

        with patch.dict('sys.modules', {'googlesearch': mock_googlesearch}):
            from tools.internet_google_webscrape import execute

            result = execute({'query': 'test'})

            assert result['success'] is False
            assert 'Search failed' in result['error']


class TestInternetGoogleAPICoverage:
    """Test error cases and missing paths in internet_google_api."""

    def test_execute_with_mocked_api(self):
        """Test successful search with mocked Google API."""
        import os
        os.environ['GOOGLE_API_KEY'] = 'test-key'
        os.environ['GOOGLE_CSE_ID'] = 'test-cse-id'

        try:
            # Mock googleapiclient
            mock_discovery = MagicMock()
            mock_service = MagicMock()
            mock_cse = MagicMock()
            mock_list = MagicMock()

            mock_response = {
                'items': [
                    {
                        'title': 'Test Result 1',
                        'link': 'https://example.com/1',
                        'snippet': 'Test description 1'
                    },
                    {
                        'title': 'Test Result 2',
                        'link': 'https://example.com/2',
                        'snippet': 'Test description 2'
                    }
                ]
            }

            mock_list.execute.return_value = mock_response
            mock_cse.list.return_value = mock_list
            mock_service.cse.return_value = mock_cse
            mock_discovery.build.return_value = mock_service

            # Mock the module
            mock_googleapiclient = MagicMock()
            mock_googleapiclient.discovery = mock_discovery

            with patch.dict('sys.modules', {'googleapiclient': mock_googleapiclient, 'googleapiclient.discovery': mock_discovery}):
                from tools.internet_google_api import execute

                result = execute({'query': 'test query', 'max_results': 5})

                assert result['success'] is True
                assert result['query'] == 'test query'
                assert result['num_results'] == 2
                assert len(result['results']) == 2
                assert result['results'][0]['title'] == 'Test Result 1'
        finally:
            os.environ.pop('GOOGLE_API_KEY', None)
            os.environ.pop('GOOGLE_CSE_ID', None)

    def test_execute_max_results_clamping(self):
        """Test that max_results is clamped to valid range."""
        import os
        os.environ['GOOGLE_API_KEY'] = 'test-key'
        os.environ['GOOGLE_CSE_ID'] = 'test-cse-id'

        try:
            mock_discovery = MagicMock()
            mock_service = MagicMock()
            mock_cse = MagicMock()
            mock_list = MagicMock()

            mock_list.execute.return_value = {'items': []}
            mock_cse.list.return_value = mock_list
            mock_service.cse.return_value = mock_cse
            mock_discovery.build.return_value = mock_service

            mock_googleapiclient = MagicMock()
            mock_googleapiclient.discovery = mock_discovery

            with patch.dict('sys.modules', {'googleapiclient': mock_googleapiclient, 'googleapiclient.discovery': mock_discovery}):
                from tools.internet_google_api import execute

                # Test upper bound (should be clamped to 10 - Google API limit)
                result = execute({'query': 'test', 'max_results': 100})
                assert result['success'] is True
                call_args = mock_cse.list.call_args
                assert call_args[1]['num'] == 10

                # Test lower bound
                result = execute({'query': 'test', 'max_results': 0})
                assert result['success'] is True
                call_args = mock_cse.list.call_args
                assert call_args[1]['num'] == 1
        finally:
            os.environ.pop('GOOGLE_API_KEY', None)
            os.environ.pop('GOOGLE_CSE_ID', None)

    def test_execute_api_exception(self):
        """Test handling of API exceptions."""
        import os
        os.environ['GOOGLE_API_KEY'] = 'test-key'
        os.environ['GOOGLE_CSE_ID'] = 'test-cse-id'

        try:
            mock_discovery = MagicMock()
            mock_discovery.build.side_effect = Exception("API error")

            mock_googleapiclient = MagicMock()
            mock_googleapiclient.discovery = mock_discovery

            with patch.dict('sys.modules', {'googleapiclient': mock_googleapiclient, 'googleapiclient.discovery': mock_discovery}):
                from tools.internet_google_api import execute

                result = execute({'query': 'test'})

                assert result['success'] is False
                assert 'Search failed' in result['error']
        finally:
            os.environ.pop('GOOGLE_API_KEY', None)
            os.environ.pop('GOOGLE_CSE_ID', None)
