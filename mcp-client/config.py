"""
Configuration for the Simple MCP Client
"""

import os
import pathlib
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Server Configuration (Direct connection)
SERVER_COMMAND = os.getenv("SERVER_COMMAND", "python")
SERVER_ARGS = os.getenv("SERVER_ARGS", "../server.py").split(",")
SERVER_CWD = pathlib.Path(__file__).parent.parent  # Go up to project root

# Proxy Configuration (For development server)
USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
PROXY_URL = os.getenv("PROXY_URL", "http://localhost:6277")
PROXY_TOKEN = os.getenv("PROXY_TOKEN")

# Connection Configuration
CONNECTION_TIMEOUT = int(os.getenv("CONNECTION_TIMEOUT", "30"))  # seconds
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# Output Configuration
PRETTY_PRINT = os.getenv("PRETTY_PRINT", "true").lower() == "true"
SHOW_TIMESTAMPS = os.getenv("SHOW_TIMESTAMPS", "true").lower() == "true"
SHOW_TOOL_DETAILS = os.getenv("SHOW_TOOL_DETAILS", "true").lower() == "true"

# Interactive Mode Configuration
PROMPT_COLOR = os.getenv("PROMPT_COLOR", "cyan")
ERROR_COLOR = os.getenv("ERROR_COLOR", "red")
SUCCESS_COLOR = os.getenv("SUCCESS_COLOR", "green")
INFO_COLOR = os.getenv("INFO_COLOR", "blue")

# Tool Configuration
DEFAULT_TOOLS = os.getenv("DEFAULT_TOOLS", "list_notes,read_note").split(",")

def get_server_config() -> dict:
    """Get server configuration for MCP connection."""
    return {
        "command": SERVER_COMMAND,
        "args": SERVER_ARGS,
        "cwd": str(SERVER_CWD),
        "env": {
            "PYTHONPATH": str(SERVER_CWD)
        }
    }

def get_proxy_config() -> dict:
    """Get proxy configuration for development server."""
    return {
        "url": PROXY_URL,
        "token": PROXY_TOKEN,
        "use_proxy": USE_PROXY
    }

def get_config_summary() -> dict:
    """Get a summary of the current configuration."""
    return {
        "server_command": SERVER_COMMAND,
        "server_args": SERVER_ARGS,
        "use_proxy": USE_PROXY,
        "proxy_url": PROXY_URL,
        "connection_timeout": CONNECTION_TIMEOUT,
        "max_retries": MAX_RETRIES,
        "pretty_print": PRETTY_PRINT,
        "show_timestamps": SHOW_TIMESTAMPS,
        "show_tool_details": SHOW_TOOL_DETAILS
    } 