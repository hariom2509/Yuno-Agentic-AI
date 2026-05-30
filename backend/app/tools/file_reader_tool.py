"""
Sandboxed file reader tool.

Reads text files (.txt, .csv, .json, .md) from a controlled workspace directory.
Validates paths to prevent directory traversal attacks.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

# Restrict to a safe directory inside the container
ALLOWED_DIR = os.getenv("FILE_READER_DIR", "/app/workspace")
ALLOWED_EXTENSIONS = {".txt", ".csv", ".json", ".md", ".log"}
MAX_FILE_SIZE = 50_000  # 50KB


def read_file(path: str) -> str:
    """
    Reads a file from the workspace directory.
    Returns file content as string, or an error message if the file
    is inaccessible, too large, or outside the allowed directory.
    """
    try:
        # Normalize and resolve path
        if not os.path.isabs(path):
            path = os.path.join(ALLOWED_DIR, path)

        resolved = os.path.realpath(path)

        # Security: prevent directory traversal
        if not resolved.startswith(os.path.realpath(ALLOWED_DIR)):
            return f"Access denied: path '{path}' is outside the allowed directory."

        # Check extension
        _, ext = os.path.splitext(resolved)
        if ext.lower() not in ALLOWED_EXTENSIONS:
            return f"Unsupported file type: '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

        # Check existence
        if not os.path.exists(resolved):
            return f"File not found: '{path}'"

        # Check size
        size = os.path.getsize(resolved)
        if size > MAX_FILE_SIZE:
            return f"File too large: {size} bytes (max {MAX_FILE_SIZE})"

        # Read
        with open(resolved, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Format based on type
        if ext == ".json":
            try:
                parsed = json.loads(content)
                return json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                return content

        return content

    except Exception as e:
        logger.error(f"File reader error: {e}")
        return f"Error reading file: {str(e)}"