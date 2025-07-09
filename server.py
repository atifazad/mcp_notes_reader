#!/usr/bin/env python3
"""
Simple MCP Note Reader Server

A basic MCP server that allows AI models to read text files from a local notes folder.
"""

import os
import pathlib
from typing import Any, Dict, List

from mcp.server.fastmcp import FastMCP
from config import (
    SERVER_NAME, 
    SERVER_VERSION, 
    NOTES_FOLDER, 
    SUPPORTED_EXTENSIONS,
    MAX_FILE_SIZE,
    ENCODING,
    validate_config,
    get_supported_files
)

# Create the MCP server
mcp = FastMCP(SERVER_NAME)

@mcp.tool()
def list_notes() -> List[Dict[str, Any]]:
    """
    List all available text files in the notes folder.
    
    Returns a list of text files with their names and basic information.
    """
    try:
        # Validate configuration
        validate_config()
        
        # Get supported files
        files = get_supported_files()
        
        notes = []
        for file_path in files:
            try:
                stat = file_path.stat()
                notes.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "extension": file_path.suffix
                })
            except OSError as e:
                # Skip files we can't access
                continue
        
        return notes
    except Exception as e:
        raise ValueError(f"Error listing notes: {str(e)}")

@mcp.tool()
def read_note(filename: str) -> str:
    """
    Read the content of a specific text file.
    
    Args:
        filename: The name of the file to read (must be a .txt file)
    
    Returns:
        The content of the file as a string
    """
    try:
        # Validate configuration
        validate_config()
        
        # Validate filename
        if not any(filename.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            raise ValueError(f"Only {', '.join(SUPPORTED_EXTENSIONS)} files are supported")
        
        # Construct file path
        file_path = NOTES_FOLDER / filename
        
        # Check if file exists
        if not file_path.exists():
            raise ValueError(f"File '{filename}' not found in notes folder")
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"File '{filename}' is too large ({file_size} bytes > {MAX_FILE_SIZE} bytes)")
        
        # Read and return file content
        with open(file_path, 'r', encoding=ENCODING) as f:
            content = f.read()
        
        return content
    except Exception as e:
        raise ValueError(f"Error reading file '{filename}': {str(e)}")

if __name__ == "__main__":
    # Run the server
    mcp.run() 