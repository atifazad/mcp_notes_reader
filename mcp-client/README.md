# Simple MCP Client

A basic MCP client for testing and interacting with MCP servers.

## Features

- **MCP Protocol Support** - Connect to any MCP server
- **Tool Discovery** - Automatically find available tools
- **Tool Execution** - Call tools and display results
- **Interactive Mode** - Command-line interface for testing
- **Error Handling** - Graceful handling of connection issues

## Setup

```bash
# Create virtual environment
uv venv --python 3.13

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

## Usage

### Basic Commands
```bash
# List available tools
python client.py list-tools

# List notes from server
python client.py list-notes

# Read a specific note
python client.py read-note meeting.txt

# Interactive mode
python client.py interactive
```

### Configuration
Edit `config.py` to change server settings:
- Server command and arguments
- Connection timeout
- Output formatting


## Development

This client is designed to work with the Simple MCP Note Reader Server. 