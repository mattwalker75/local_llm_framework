"""
Execute function for file access tool.

This imports from __init__.py to avoid code duplication.
"""

from . import execute as _execute

# Re-export the execute function
execute = _execute
