"""
Unit tests for modules/text2speech/list_voices.py module.

Tests the standalone voice listing utility script.
"""

import pytest
import json
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from argparse import Namespace


@pytest.fixture
def mock_tts_with_voices():
    """Create a mock TextToSpeech instance with sample voices."""
    mock_tts = MagicMock()
    mock_voices = [
        {
            'id': 'com.apple.speech.synthesis.voice.samantha',
            'name': 'Samantha',
            'languages': ['en-US']
        },
        {
            'id': 'com.apple.speech.synthesis.voice.alex',
            'name': 'Alex',
            'languages': ['en-US', 'en-GB']
        },
        {
            'id': 'com.apple.speech.synthesis.voice.amelie',
            'name': 'Amelie',
            'languages': ['fr-FR']
        }
    ]
    mock_tts.get_available_voices.return_value = mock_voices
    return mock_tts


@pytest.fixture
def mock_tts_no_voices():
    """Create a mock TextToSpeech instance with no voices."""
    mock_tts = MagicMock()
    mock_tts.get_available_voices.return_value = []
    return mock_tts


class TestListVoicesTable:
    """Test list_voices_table function."""

    def test_list_voices_table_displays_all_voices(self, mock_tts_with_voices):
        """Test table format displays all voice information (lines 25-52)."""
        from modules.text2speech.list_voices import list_voices_table

        with patch('modules.text2speech.list_voices.TextToSpeech', return_value=mock_tts_with_voices):
            # Capture stdout
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                list_voices_table()
                output = captured_output.getvalue()
            finally:
                sys.stdout = sys.__stdout__

            # Verify header
            assert "Available Text-to-Speech Voices" in output
            assert "=" * 80 in output

            # Verify all voices are displayed
            assert "1. Samantha" in output
            assert "2. Alex" in output
            assert "3. Amelie" in output

            # Verify IDs are shown
            assert "ID: com.apple.speech.synthesis.voice.samantha" in output
            assert "ID: com.apple.speech.synthesis.voice.alex" in output

            # Verify languages are shown
            assert "Languages: en-US" in output
            assert "Languages: en-US, en-GB" in output
            assert "Languages: fr-FR" in output

            # Verify footer with count
            assert "Total: 3 voice(s) available" in output

            # Verify usage instructions
            assert "To use a voice, copy its ID" in output

    def test_list_voices_table_empty_list(self, mock_tts_no_voices):
        """Test table format handles empty voice list (lines 34-36)."""
        from modules.text2speech.list_voices import list_voices_table

        with patch('modules.text2speech.list_voices.TextToSpeech', return_value=mock_tts_no_voices):
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                list_voices_table()
                output = captured_output.getvalue()
            finally:
                sys.stdout = sys.__stdout__

            # Should display "no voices" message
            assert "No voices found on this system." in output

    def test_list_voices_table_voice_without_languages(self):
        """Test table format handles voice without languages field (line 41)."""
        from modules.text2speech.list_voices import list_voices_table

        mock_tts = MagicMock()
        mock_tts.get_available_voices.return_value = [
            {
                'id': 'test.voice',
                'name': 'Test Voice',
                'languages': []  # Empty languages list
            }
        ]

        with patch('modules.text2speech.list_voices.TextToSpeech', return_value=mock_tts):
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                list_voices_table()
                output = captured_output.getvalue()
            finally:
                sys.stdout = sys.__stdout__

            # Should still display the voice
            assert "Test Voice" in output
            assert "ID: test.voice" in output

    def test_list_voices_table_languages_as_string(self):
        """Test table format handles languages as string (line 42)."""
        from modules.text2speech.list_voices import list_voices_table

        mock_tts = MagicMock()
        mock_tts.get_available_voices.return_value = [
            {
                'id': 'test.voice',
                'name': 'Test Voice',
                'languages': 'en-US'  # String instead of list
            }
        ]

        with patch('modules.text2speech.list_voices.TextToSpeech', return_value=mock_tts):
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                list_voices_table()
                output = captured_output.getvalue()
            finally:
                sys.stdout = sys.__stdout__

            # Should display language correctly
            assert "Languages: en-US" in output


class TestListVoicesJson:
    """Test list_voices_json function."""

    def test_list_voices_json_valid_output(self, mock_tts_with_voices):
        """Test JSON format produces valid JSON output (lines 54-64)."""
        from modules.text2speech.list_voices import list_voices_json

        with patch('modules.text2speech.list_voices.TextToSpeech', return_value=mock_tts_with_voices):
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                list_voices_json()
                output = captured_output.getvalue()
            finally:
                sys.stdout = sys.__stdout__

            # Parse JSON to verify validity
            data = json.loads(output)

            # Verify structure
            assert 'total_voices' in data
            assert 'voices' in data
            assert data['total_voices'] == 3
            assert len(data['voices']) == 3

            # Verify voice data
            assert data['voices'][0]['name'] == 'Samantha'
            assert data['voices'][1]['name'] == 'Alex'
            assert data['voices'][2]['name'] == 'Amelie'

    def test_list_voices_json_empty_list(self, mock_tts_no_voices):
        """Test JSON format with no voices."""
        from modules.text2speech.list_voices import list_voices_json

        with patch('modules.text2speech.list_voices.TextToSpeech', return_value=mock_tts_no_voices):
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                list_voices_json()
                output = captured_output.getvalue()
            finally:
                sys.stdout = sys.__stdout__

            # Parse JSON
            data = json.loads(output)

            # Should have zero voices
            assert data['total_voices'] == 0
            assert data['voices'] == []


class TestListVoicesSimple:
    """Test list_voices_simple function."""

    def test_list_voices_simple_format(self, mock_tts_with_voices):
        """Test simple format output (lines 67-73)."""
        from modules.text2speech.list_voices import list_voices_simple

        with patch('modules.text2speech.list_voices.TextToSpeech', return_value=mock_tts_with_voices):
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                list_voices_simple()
                output = captured_output.getvalue()
            finally:
                sys.stdout = sys.__stdout__

            # Verify simple format: "Name | ID"
            lines = output.strip().split('\n')
            assert len(lines) == 3

            assert "Samantha | com.apple.speech.synthesis.voice.samantha" in output
            assert "Alex | com.apple.speech.synthesis.voice.alex" in output
            assert "Amelie | com.apple.speech.synthesis.voice.amelie" in output

    def test_list_voices_simple_empty_list(self, mock_tts_no_voices):
        """Test simple format with no voices."""
        from modules.text2speech.list_voices import list_voices_simple

        with patch('modules.text2speech.list_voices.TextToSpeech', return_value=mock_tts_no_voices):
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                list_voices_simple()
                output = captured_output.getvalue()
            finally:
                sys.stdout = sys.__stdout__

            # Should produce no output (or empty)
            assert output.strip() == ""


class TestMain:
    """Test main function and CLI argument parsing."""

    def test_main_default_table_format(self, mock_tts_with_voices):
        """Test main() defaults to table format (lines 76-104)."""
        from modules.text2speech.list_voices import main

        with patch('modules.text2speech.list_voices.TextToSpeech', return_value=mock_tts_with_voices):
            with patch('sys.argv', ['list_voices.py']):
                captured_output = StringIO()
                sys.stdout = captured_output

                try:
                    main()
                    output = captured_output.getvalue()
                finally:
                    sys.stdout = sys.__stdout__

                # Should use table format by default
                assert "Available Text-to-Speech Voices" in output
                assert "Total: 3 voice(s) available" in output

    def test_main_json_format(self, mock_tts_with_voices):
        """Test main() with --format json (line 100)."""
        from modules.text2speech.list_voices import main

        with patch('modules.text2speech.list_voices.TextToSpeech', return_value=mock_tts_with_voices):
            with patch('sys.argv', ['list_voices.py', '--format', 'json']):
                captured_output = StringIO()
                sys.stdout = captured_output

                try:
                    main()
                    output = captured_output.getvalue()
                finally:
                    sys.stdout = sys.__stdout__

                # Should produce valid JSON
                data = json.loads(output)
                assert data['total_voices'] == 3

    def test_main_simple_format(self, mock_tts_with_voices):
        """Test main() with --format simple (line 102)."""
        from modules.text2speech.list_voices import main

        with patch('modules.text2speech.list_voices.TextToSpeech', return_value=mock_tts_with_voices):
            with patch('sys.argv', ['list_voices.py', '--format', 'simple']):
                captured_output = StringIO()
                sys.stdout = captured_output

                try:
                    main()
                    output = captured_output.getvalue()
                finally:
                    sys.stdout = sys.__stdout__

                # Should use simple format
                assert "Samantha | com.apple.speech.synthesis.voice.samantha" in output

    def test_main_format_short_flag(self, mock_tts_with_voices):
        """Test main() with -f short flag."""
        from modules.text2speech.list_voices import main

        with patch('modules.text2speech.list_voices.TextToSpeech', return_value=mock_tts_with_voices):
            with patch('sys.argv', ['list_voices.py', '-f', 'json']):
                captured_output = StringIO()
                sys.stdout = captured_output

                try:
                    main()
                    output = captured_output.getvalue()
                finally:
                    sys.stdout = sys.__stdout__

                # Should produce JSON
                data = json.loads(output)
                assert 'total_voices' in data

    def test_main_exception_handling(self, mock_tts_with_voices):
        """Test main() catches exceptions and exits with error code (lines 106-108)."""
        from modules.text2speech.list_voices import main

        # Make TextToSpeech raise an exception
        with patch('modules.text2speech.list_voices.TextToSpeech', side_effect=Exception("TTS Error")):
            with patch('sys.argv', ['list_voices.py']):
                with patch('sys.exit') as mock_exit:
                    captured_output = StringIO()
                    sys.stderr = captured_output

                    try:
                        main()
                    finally:
                        sys.stderr = sys.__stderr__

                    # Should write error to stderr
                    error_output = captured_output.getvalue()
                    assert "Error: TTS Error" in error_output

                    # Should call sys.exit(1)
                    mock_exit.assert_called_once_with(1)


class TestScriptAsMain:
    """Test script execution as __main__."""

    def test_script_calls_main_when_run_directly(self):
        """Test that running the script calls main() (line 112)."""
        # Import the module and check if __name__ == "__main__" block works
        # This is more of a structural test

        import modules.text2speech.list_voices as list_voices_module

        # Verify main function exists and is callable
        assert hasattr(list_voices_module, 'main')
        assert callable(list_voices_module.main)

        # Verify all required functions exist
        assert hasattr(list_voices_module, 'list_voices_table')
        assert hasattr(list_voices_module, 'list_voices_json')
        assert hasattr(list_voices_module, 'list_voices_simple')
