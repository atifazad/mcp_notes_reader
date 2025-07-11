#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project directory
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..." >&2
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment (venv)..." >&2
    source venv/bin/activate
else
    echo "Error: Virtual environment not found. Please create one with 'uv venv' or 'python -m venv venv'" >&2
    exit 1
fi

# Check if required dependencies are installed
if ! python -c "import mcp" 2>/dev/null; then
    echo "Installing dependencies..." >&2
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt >&2
    else
        echo "Error: requirements.txt not found" >&2
        exit 1
    fi
fi

# Start the MCP server directly
echo "Starting MCP server..." >&2
exec python server.py 