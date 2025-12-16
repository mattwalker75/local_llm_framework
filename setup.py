"""
Setup script for Local LLM Framework.

This allows LLF to be installed as a package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        # Filter out development dependencies and comments
        requirements = [
            line.strip()
            for line in f
            if line.strip()
            and not line.startswith('#')
            and not line.startswith('pytest')
            and not line.startswith('black')
            and not line.startswith('flake8')
            and not line.startswith('mypy')
        ]
else:
    requirements = []

setup(
    name="local-llm-framework",
    version="0.1.0",
    author="LLF Development Team",
    author_email="",
    description="A Python framework for running Large Language Models locally using vLLM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=8.0.0',
            'pytest-cov>=4.1.0',
            'pytest-mock>=3.12.0',
            'black>=24.0.0',
            'flake8>=7.0.0',
            'mypy>=1.8.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'llf=llf.cli:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
