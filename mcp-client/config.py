"""
Configuration for the Simple MCP Client
"""

import pathlib
from typing import List

# Server Configuration (Direct connection)
SERVER_COMMAND = "python"
SERVER_ARGS = ["../server.py"]
SERVER_CWD = pathlib.Path(__file__).parent.parent  # Go up to project root

# Proxy Configuration (For development server)
USE_PROXY = True
PROXY_URL = "http://localhost:6277"
PROXY_TOKEN = "fc807c506aecc4f56eefab768dcca4b29d8a808d311be12020c92042bf21e09f"

# Connection Configuration
CONNECTION_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Output Configuration
PRETTY_PRINT = True
SHOW_TIMESTAMPS = True
SHOW_TOOL_DETAILS = True

# Interactive Mode Configuration
PROMPT_COLOR = "cyan"
ERROR_COLOR = "red"
SUCCESS_COLOR = "green"
INFO_COLOR = "blue"

# Tool Configuration
DEFAULT_TOOLS = ["list_notes", "read_note"]

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