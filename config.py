"""
Configuration for the Simple MCP Note Reader Server
"""

import pathlib
from typing import Optional

# Server Configuration
SERVER_NAME = "Simple Note Reader"
SERVER_VERSION = "1.0.0"

# File System Configuration
NOTES_FOLDER = pathlib.Path("notes")
SUPPORTED_EXTENSIONS = [".txt"]

# Tool Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
ENCODING = "utf-8"

def validate_config() -> None:
    """Validate the configuration settings."""
    if not NOTES_FOLDER.exists():
        raise ValueError(f"Notes folder '{NOTES_FOLDER}' does not exist")
    
    if not NOTES_FOLDER.is_dir():
        raise ValueError(f"'{NOTES_FOLDER}' is not a directory")

def get_supported_files() -> list[pathlib.Path]:
    """Get all supported files from the notes folder."""
    if not NOTES_FOLDER.exists():
        return []
    
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(NOTES_FOLDER.glob(f"*{ext}"))
    
    return sorted(files) 