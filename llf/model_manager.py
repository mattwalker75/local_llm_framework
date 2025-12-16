"""
Model management module for Local LLM Framework.

This module handles downloading, verifying, and managing LLM models locally.

Design: Built to support multiple models and model sources (HuggingFace, local paths).
Future: Can be extended to support model versioning, updates, and cleanup.
"""

import os
from pathlib import Path
from typing import Optional, Dict
import shutil

from huggingface_hub import snapshot_download, HfApi
from huggingface_hub.utils import HfHubHTTPError

from .logging_config import get_logger
from .config import Config

logger = get_logger(__name__)


class ModelManager:
    """
    Manages LLM models: downloading, verification, and storage.

    Responsibilities:
    - Check if model exists locally
    - Download models from HuggingFace Hub
    - Verify model integrity
    - Provide model path for runtime loading
    """

    def __init__(self, config: Config):
        """
        Initialize model manager.

        Args:
            config: Configuration instance containing model settings.
        """
        self.config = config
        self.model_dir = config.model_dir
        self.cache_dir = config.cache_dir

        # Ensure directories exist
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # HuggingFace API client
        self.hf_api = HfApi()

    def get_model_path(self, model_name: Optional[str] = None) -> Path:
        """
        Get the local path for a model.

        Args:
            model_name: Model identifier (e.g., "Qwen/Qwen3-Coder-30B-A3B-Instruct").
                       If None, uses config's default model.

        Returns:
            Path to the model directory.
        """
        if model_name is None:
            model_name = self.config.model_name

        # Convert model name to safe directory name
        # Replace / with -- to avoid directory nesting
        safe_name = model_name.replace("/", "--")
        return self.model_dir / safe_name

    def is_model_downloaded(self, model_name: Optional[str] = None) -> bool:
        """
        Check if a model is already downloaded locally.

        Args:
            model_name: Model identifier. If None, uses config's default model.

        Returns:
            True if model exists locally and appears valid, False otherwise.
        """
        model_path = self.get_model_path(model_name)

        if not model_path.exists():
            return False

        # Basic validation: check for common model files
        # Most models should have at least a config.json
        required_files = ["config.json"]
        for file_name in required_files:
            if not (model_path / file_name).exists():
                logger.warning(
                    f"Model directory exists but missing {file_name}: {model_path}"
                )
                return False

        return True

    def download_model(
        self,
        model_name: Optional[str] = None,
        force: bool = False,
        token: Optional[str] = None
    ) -> Path:
        """
        Download a model from HuggingFace Hub.

        Args:
            model_name: Model identifier. If None, uses config's default model.
            force: If True, re-download even if model exists locally.
            token: Optional HuggingFace API token for private models.

        Returns:
            Path to the downloaded model directory.

        Raises:
            ValueError: If model download fails.
        """
        if model_name is None:
            model_name = self.config.model_name

        model_path = self.get_model_path(model_name)

        # Check if already downloaded
        if not force and self.is_model_downloaded(model_name):
            logger.info(f"Model already downloaded: {model_path}")
            return model_path

        logger.info(f"Downloading model: {model_name}")
        logger.info(f"Destination: {model_path}")

        try:
            # Download model from HuggingFace Hub
            downloaded_path = snapshot_download(
                repo_id=model_name,
                local_dir=model_path,
                local_dir_use_symlinks=False,  # Copy files instead of symlinking
                cache_dir=self.cache_dir,
                token=token,
                resume_download=True,  # Resume if interrupted
            )

            logger.info(f"Model downloaded successfully: {downloaded_path}")
            return Path(downloaded_path)

        except HfHubHTTPError as e:
            error_msg = f"Failed to download model {model_name}: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

        except Exception as e:
            error_msg = f"Unexpected error downloading model {model_name}: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def verify_model(self, model_name: Optional[str] = None) -> Dict[str, bool]:
        """
        Verify model integrity with detailed checks.

        Args:
            model_name: Model identifier. If None, uses config's default model.

        Returns:
            Dictionary with verification results:
            {
                'exists': bool,
                'has_config': bool,
                'has_tokenizer': bool,
                'has_weights': bool,
                'valid': bool  # Overall validity
            }
        """
        if model_name is None:
            model_name = self.config.model_name

        model_path = self.get_model_path(model_name)
        results = {
            'exists': model_path.exists(),
            'has_config': False,
            'has_tokenizer': False,
            'has_weights': False,
            'valid': False,
        }

        if not results['exists']:
            return results

        # Check for config.json
        results['has_config'] = (model_path / "config.json").exists()

        # Check for tokenizer files (various formats)
        tokenizer_files = [
            "tokenizer.json",
            "tokenizer_config.json",
            "vocab.json",
        ]
        results['has_tokenizer'] = any(
            (model_path / f).exists() for f in tokenizer_files
        )

        # Check for model weight files (various formats)
        weight_patterns = [
            "*.safetensors",
            "*.bin",
            "pytorch_model*.bin",
            "model*.safetensors",
        ]
        weight_files = []
        for pattern in weight_patterns:
            weight_files.extend(model_path.glob(pattern))

        results['has_weights'] = len(weight_files) > 0

        # Overall validity
        results['valid'] = all([
            results['exists'],
            results['has_config'],
            results['has_tokenizer'],
            results['has_weights'],
        ])

        return results

    def delete_model(self, model_name: Optional[str] = None) -> bool:
        """
        Delete a model from local storage.

        Args:
            model_name: Model identifier. If None, uses config's default model.

        Returns:
            True if deletion successful, False otherwise.
        """
        if model_name is None:
            model_name = self.config.model_name

        model_path = self.get_model_path(model_name)

        if not model_path.exists():
            logger.warning(f"Model not found, nothing to delete: {model_path}")
            return False

        try:
            shutil.rmtree(model_path)
            logger.info(f"Deleted model: {model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete model {model_path}: {e}")
            return False

    def list_downloaded_models(self) -> list[str]:
        """
        List all models downloaded in the model directory.

        Returns:
            List of model names (in original format with /).
        """
        if not self.model_dir.exists():
            return []

        models = []
        for item in self.model_dir.iterdir():
            if item.is_dir():
                # Convert back from safe name (replace -- with /)
                original_name = item.name.replace("--", "/")
                models.append(original_name)

        return sorted(models)

    def get_model_info(self, model_name: Optional[str] = None) -> Dict:
        """
        Get detailed information about a model.

        Args:
            model_name: Model identifier. If None, uses config's default model.

        Returns:
            Dictionary with model information.
        """
        if model_name is None:
            model_name = self.config.model_name

        model_path = self.get_model_path(model_name)
        verification = self.verify_model(model_name)

        info = {
            'name': model_name,
            'path': str(model_path),
            'downloaded': verification['valid'],
            'verification': verification,
        }

        # Get size if model exists
        if model_path.exists():
            total_size = sum(
                f.stat().st_size
                for f in model_path.rglob('*')
                if f.is_file()
            )
            info['size_bytes'] = total_size
            info['size_gb'] = round(total_size / (1024 ** 3), 2)

        return info
