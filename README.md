# Simple MCP Note Reader

A basic MCP server that allows AI models to read text files from a local notes folder.

## Features

- **List Notes**: Shows all available `.txt` files in the notes folder
- **Read Note**: Reads and returns the content of a specific text file
- **Read PDF**: Reads and extracts text from PDF files
- **Google Calendar Integration**: Create and list calendar events

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment with Python 3.13+
uv venv --python 3.13

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Run the setup script (recommended)
python setup_env.py

# Or manually copy the example environment file
cp env.example .env

# Edit the .env file with your settings
nano .env
```

**Important Environment Variables:**
- `NOTES_FOLDER`: Path to your notes directory (default: `notes`)
- `SUPPORTED_EXTENSIONS`: Comma-separated list of file extensions (default: `.txt,.pdf`)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: `10485760` for 10MB)
- `GOOGLE_CLIENT_ID`: Your Google API client ID
- `GOOGLE_CLIENT_SECRET`: Your Google API client secret
- `PROXY_TOKEN`: Your proxy authentication token

### 3. Add Your Notes

Place your `.txt` and `.pdf` files in the `notes/` folder:

```
notes/
├── meeting.txt
├── ideas.txt
├── cv.pdf
└── todo.txt
```

### 4. Test the Server

```bash
# Start development server with web interface
mcp dev server.py
```

Then open your browser to `http://localhost:6274` to test the tools.

### 5. Use with Claude Desktop

Add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "simple-note-reader": {
      "command": "./start_server.sh",
      "args": [],
      "cwd": "/path/to/your/project"
    }
  }
}
```

**Note**: The `start_server.sh` script automatically activates your virtual environment and installs dependencies if needed. Make sure the script is executable (`chmod +x start_server.sh`).

If you prefer to use the direct Python command (without virtual environment), use:

```json
{
  "mcpServers": {
    "simple-note-reader": {
      "command": "python3",
      "args": ["server.py"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

## Usage Examples

### Ask Claude to list your notes:
"What notes do I have?"

### Ask Claude to read a specific file:
"Read my meeting.txt file"

### Ask Claude to summarize a note:
"Summarize the content of ideas.txt"

### Ask Claude to create a calendar event:
"Create a calendar event for tomorrow at 2pm called 'Team Meeting'"

## Configuration

### Environment Variables

The application uses environment variables for configuration. Copy `env.example` to `.env` and customize:

```bash
# Server Configuration
SERVER_NAME=Simple Note Reader
SERVER_VERSION=1.0.0

# File System Configuration
NOTES_FOLDER=notes
SUPPORTED_EXTENSIONS=.txt,.pdf
MAX_FILE_SIZE=10485760
ENCODING=utf-8

# Google Calendar API Configuration
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_SCOPES=https://www.googleapis.com/auth/calendar

# Security Configuration
DEBUG=false
LOG_LEVEL=INFO
```

### Security Best Practices

1. **Never commit `.env` files** - They're already in `.gitignore`
2. **Use strong credentials** - Generate unique tokens for each environment
3. **Rotate credentials regularly** - Update API keys and tokens periodically
4. **Use different credentials** - Separate development and production credentials
5. **Set proper file permissions** - Token files are automatically secured

## Development

### Testing
```bash
mcp dev server.py  # Web interface for testing
```

### Adding New Tools
1. Add function with `@mcp.tool()` decorator
2. Update documentation
3. Test with `mcp dev`

### Configuration Management
```python
# Get current configuration
from config import get_config_summary
config = get_config_summary()
print(config)
```

## Security Features

- **Environment-based configuration**: No hardcoded secrets
- **Secure file permissions**: Token files are automatically secured (600)
- **Input validation**: All inputs are validated and sanitized
- **Error handling**: Secure error messages without information disclosure
- **Path validation**: Prevents directory traversal attacks

## Limitations

- **Read-only**: Cannot create or modify files
- **Text files only**: Only supports `.txt` and `.pdf` files
- **Local files only**: Cannot access remote files
- **Size limits**: Files must be under the configured size limit 