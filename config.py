"""
Configuration for the Simple MCP Note Reader Server
"""

import os
import pathlib
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Server Configuration
SERVER_NAME = os.getenv("SERVER_NAME", "Simple Note Reader")
SERVER_VERSION = os.getenv("SERVER_VERSION", "1.0.0")

# File System Configuration
NOTES_FOLDER = pathlib.Path(os.getenv("NOTES_FOLDER", "notes"))
SUPPORTED_EXTENSIONS = os.getenv("SUPPORTED_EXTENSIONS", ".txt,.pdf").split(",")

# Tool Configuration
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB default
ENCODING = os.getenv("ENCODING", "utf-8")

# Security Configuration
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

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

def get_config_summary() -> dict:
    """Get a summary of the current configuration."""
    return {
        "server_name": SERVER_NAME,
        "server_version": SERVER_VERSION,
        "notes_folder": str(NOTES_FOLDER),
        "supported_extensions": SUPPORTED_EXTENSIONS,
        "max_file_size": MAX_FILE_SIZE,
        "encoding": ENCODING,
        "debug": DEBUG,
        "log_level": LOG_LEVEL
    } 