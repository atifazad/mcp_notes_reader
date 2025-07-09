# Simple MCP Note Reader

A basic MCP server that allows AI models to read text files from a local notes folder.

## Features

- **List Notes**: Shows all available `.txt` files in the notes folder
- **Read Note**: Reads and returns the content of a specific text file
- **Error Handling**: Robust validation and error messages
- **Configurable**: Easy to customize file types, paths, and limits

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

### 2. Add Your Notes

Place your `.txt` files in the `notes/` folder:

```
notes/
├── meeting.txt
├── ideas.txt
└── todo.txt
```

### 3. Test the Server

```bash
# Start development server with web interface
mcp dev server.py
```

Then open your browser to `http://localhost:6274` to test the tools.

### 4. Use with Claude Desktop

Add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "simple-note-reader": {
      "command": "python",
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

## Configuration

Edit `config.py` to customize:

- **File types**: Change `SUPPORTED_EXTENSIONS`
- **File size limit**: Adjust `MAX_FILE_SIZE`
- **Notes folder**: Modify `NOTES_FOLDER`
- **Encoding**: Change `ENCODING`


## Development

### Testing
```bash
mcp dev server.py  # Web interface for testing
```

### Adding New Tools
1. Add function with `@mcp.tool()` decorator
2. Update documentation
3. Test with `mcp dev`

## Limitations

- **Read-only**: Cannot create or modify files
- **Text files only**: Only supports `.txt` files
- **Single folder**: Only reads from `notes/` directory
- **Size limit**: 10MB file size limit (configurable)

## Next Steps

Once you master this simple version:
- Add file writing capability
- Support more file types
- Add search functionality
- Implement subfolder support 