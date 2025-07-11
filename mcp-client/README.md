# Simple MCP Client

A basic MCP client for testing and interacting with MCP servers.

## Features

- **MCP Protocol Support** - Connect to any MCP server
- **Tool Discovery** - Automatically find available tools
- **Tool Execution** - Call tools and display results
- **Interactive Mode** - Command-line interface for testing
- **Error Handling** - Graceful handling of connection issues
- **Environment Configuration** - Secure configuration via `.env` files

## Setup

```bash
# Create virtual environment
uv venv --python 3.13

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Configure environment variables
cp ../env.example ../.env
# Edit ../.env with your settings
```

## Usage

### Basic Commands
```bash
# List available tools
python stdio_client.py list-tools

# List notes from server
python stdio_client.py list-notes

# Read a specific note
python stdio_client.py read-note meeting.txt

# Interactive mode
python stdio_client.py interactive
```

### Configuration
The client uses environment variables for configuration. Key variables:

```bash
# Server Configuration
SERVER_COMMAND=python
SERVER_ARGS=../server.py

# Proxy Configuration
USE_PROXY=false
PROXY_URL=http://localhost:6277
PROXY_TOKEN=your_proxy_token_here

# Connection Settings
CONNECTION_TIMEOUT=30
MAX_RETRIES=3

# Output Settings
PRETTY_PRINT=true
SHOW_TIMESTAMPS=true
SHOW_TOOL_DETAILS=true
```

### Security Features

- **Environment-based configuration**: No hardcoded secrets
- **Secure token management**: Proxy tokens stored in environment variables
- **Connection validation**: Proper error handling for connection issues
- **Input sanitization**: All inputs are validated

## Development

This client is designed to work with the Simple MCP Note Reader Server.

### Configuration Management
```python
# Get current configuration
from config import get_config_summary
config = get_config_summary()
print(config)
```

### Adding New Commands
1. Add new command function with `@cli.command()` decorator
2. Update documentation
3. Test with the server 