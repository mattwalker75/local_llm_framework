"""
Tools Configuration Manager for Local LLM Framework.

This module manages tool system features and compatibility layers.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from llf.logging_config import get_logger

logger = get_logger(__name__)


class ToolsManager:
    """Manager for tool system configuration and features."""

    def __init__(self, config_path: Optional[Path] = None, main_config_path: Optional[Path] = None):
        """
        Initialize ToolsManager.

        Args:
            config_path: Path to tools_config.json (legacy fallback). If None, uses default location.
            main_config_path: Path to main config.json. If None, uses default location.
        """
        # Main config (primary source)
        if main_config_path is None:
            self.main_config_path = Path(__file__).parent.parent / 'configs' / 'config.json'
        else:
            self.main_config_path = Path(main_config_path)

        # Legacy tools config (fallback)
        if config_path is None:
            self.config_path = Path(__file__).parent.parent / 'tools' / 'tools_config.json'
        else:
            self.config_path = Path(config_path)

        self.config = self._load_config()
        self.session_overrides = {}  # Store CLI session overrides

    def _load_config(self) -> Dict[str, Any]:
        """
        Load tools configuration from main config.json with fallback to tools_config.json.

        Priority:
        1. Main config.json (configs/config.json) - llm_endpoint.tools section
        2. Legacy tools_config.json (tools/tools_config.json)
        3. Default config
        """
        # Try main config first
        if self.main_config_path.exists():
            try:
                with open(self.main_config_path, 'r') as f:
                    main_config = json.load(f)
                    tools_config = main_config.get('llm_endpoint', {}).get('tools', {})

                    if tools_config:
                        # Convert main config format to internal format
                        return self._convert_main_config(tools_config)

            except Exception as e:
                logger.warning(f"Failed to load main config: {e}")

        # Fall back to legacy tools_config.json
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    legacy_config = json.load(f)
                    logger.info(f"Using legacy tools config from {self.config_path}")
                    return legacy_config
            except Exception as e:
                logger.error(f"Failed to load tools config: {e}")

        # Use defaults if nothing else works
        logger.warning("No tools config found, using defaults")
        return self._get_default_config()

    def _convert_main_config(self, tools_config: Dict[str, str]) -> Dict[str, Any]:
        """
        Convert main config format to internal format.

        Main config format: {"xml_format": "enable"}
        Internal format: {"features": {"xml_format": {"enabled": True, ...}}}
        """
        features = {}

        for feature_name, setting in tools_config.items():
            enabled = setting.lower() == "enable"
            features[feature_name] = {
                "enabled": enabled,
                "description": self._get_feature_description(feature_name)
            }

        return {
            "version": "1.0",
            "features": features,
            "source": "main_config"
        }

    def _get_feature_description(self, feature_name: str) -> str:
        """Get description for a feature."""
        descriptions = {
            "xml_format": "Parse XML-style function calls and convert to OpenAI JSON format"
        }
        return descriptions.get(feature_name, f"Tool feature: {feature_name}")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "version": "1.0",
            "features": {
                "xml_format": {
                    "enabled": False,
                    "description": "Parse XML-style function calls"
                }
            }
        }

    def _save_config(self) -> bool:
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save tools config: {e}")
            return False

    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled.

        Checks session override first, then config file.

        Args:
            feature_name: Name of the feature (e.g., 'xml_format')

        Returns:
            True if feature is enabled
        """
        # Check session override first
        if feature_name in self.session_overrides:
            return self.session_overrides[feature_name]

        # Fall back to config
        return self.config.get('features', {}).get(feature_name, {}).get('enabled', False)

    def enable_feature(self, feature_name: str, session_only: bool = True) -> bool:
        """
        Enable a feature.

        Args:
            feature_name: Name of the feature to enable
            session_only: If True, only affects current session (override).
                         If False, saves to legacy config file.

        Returns:
            True if successful
        """
        if session_only:
            # Session override - doesn't modify config files
            self.session_overrides[feature_name] = True
            logger.info(f"Session override: {feature_name} enabled (temporary)")
            return True
        else:
            # Persistent change to legacy config file
            if 'features' not in self.config:
                self.config['features'] = {}

            if feature_name not in self.config['features']:
                # Create new feature entry
                self.config['features'][feature_name] = {
                    'enabled': True,
                    'description': self._get_feature_description(feature_name)
                }
            else:
                self.config['features'][feature_name]['enabled'] = True

            return self._save_config()

    def disable_feature(self, feature_name: str, session_only: bool = True) -> bool:
        """
        Disable a feature.

        Args:
            feature_name: Name of the feature to disable
            session_only: If True, only affects current session (override).
                         If False, saves to legacy config file.

        Returns:
            True if successful
        """
        if session_only:
            # Session override - doesn't modify config files
            self.session_overrides[feature_name] = False
            logger.info(f"Session override: {feature_name} disabled (temporary)")
            return True
        else:
            # Persistent change to legacy config file
            if 'features' not in self.config:
                return True

            if feature_name not in self.config['features']:
                logger.error(f"Unknown feature: {feature_name}")
                return False

            self.config['features'][feature_name]['enabled'] = False
            return self._save_config()

    def reset_to_config(self, feature_name: str) -> bool:
        """
        Reset a feature to use the config file setting (remove session override).

        This is what 'auto' means in CLI - use whatever is in config.json.

        Args:
            feature_name: Name of the feature to reset

        Returns:
            True if successful
        """
        if feature_name in self.session_overrides:
            del self.session_overrides[feature_name]
            logger.info(f"Reset {feature_name} to config file setting")

        return True

    def list_features(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all features and their status.

        Returns:
            Dict of feature names to feature info
        """
        return self.config.get('features', {})
