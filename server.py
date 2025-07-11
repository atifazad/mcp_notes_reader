#!/usr/bin/env python3
"""
Simple MCP Note Reader Server

A basic MCP server that allows AI models to read text and PDF files from a local notes folder,
and create events in Google Calendar.
"""

import os
import pathlib
from typing import Any, Dict, List
from datetime import datetime, timedelta

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

from mcp.server.fastmcp import FastMCP
from config import (
    SERVER_NAME, 
    SERVER_VERSION, 
    NOTES_FOLDER, 
    SUPPORTED_EXTENSIONS,
    MAX_FILE_SIZE,
    ENCODING,
    validate_config,
    get_supported_files,
    get_config_summary
)
from google_calendar_service import get_calendar_service

# Create the MCP server
mcp = FastMCP(SERVER_NAME)

@mcp.tool()
def list_notes() -> List[Dict[str, Any]]:
    """
    List all available text and PDF files in the notes folder.
    
    Returns a list of files with their names and basic information.
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
        if not filename.endswith('.txt'):
            raise ValueError("Only .txt files are supported by this tool. Use read_pdf for PDF files.")
        
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

@mcp.tool()
def read_pdf(filename: str) -> str:
    """
    Read the content of a specific PDF file.
    
    Args:
        filename: The name of the file to read (must be a .pdf file)
    
    Returns:
        The text content of the PDF as a string
    """
    if not PDF_SUPPORT:
        raise ValueError("PDF support is not available. Please install PyPDF2: pip install PyPDF2")
    
    try:
        # Validate configuration
        validate_config()
        
        # Validate filename
        if not filename.endswith('.pdf'):
            raise ValueError("Only .pdf files are supported by this tool. Use read_note for text files.")
        
        # Construct file path
        file_path = NOTES_FOLDER / filename
        
        # Check if file exists
        if not file_path.exists():
            raise ValueError(f"File '{filename}' not found in notes folder")
        
        # Check file size
        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise ValueError(f"File '{filename}' is too large ({file_size} bytes > {MAX_FILE_SIZE} bytes)")
        
        # Read PDF content
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            # Extract text from all pages
            content = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():  # Only add non-empty pages
                    content.append(f"--- Page {page_num + 1} ---\n{text}")
            
            return "\n\n".join(content)
        
    except Exception as e:
        raise ValueError(f"Error reading PDF file '{filename}': {str(e)}")

@mcp.tool()
def create_calendar_event(summary: str, description: str = "", 
                         start_time: str = "", end_time: str = "", 
                         location: str = "") -> Dict[str, Any]:
    """
    Create an event in Google Calendar.
    
    Args:
        summary: Event title/name
        description: Event description (optional)
        start_time: Start time in ISO format (e.g., "2024-01-15T14:00:00") or empty for default
        end_time: End time in ISO format or empty for default (1 hour after start)
        location: Event location (optional)
    
    Returns:
        Dictionary with event details or error information
    """
    try:
        calendar_service = get_calendar_service()
        if not calendar_service:
            return {"error": "Google Calendar service not available. Please check credentials."}
        
        # Parse start and end times
        start_dt = None
        end_dt = None
        
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                return {"error": f"Invalid start_time format: {start_time}. Use ISO format (e.g., '2024-01-15T14:00:00')"}
        
        if end_time:
            try:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                return {"error": f"Invalid end_time format: {end_time}. Use ISO format (e.g., '2024-01-15T15:00:00')"}
        
        result = calendar_service.create_event(
            summary=summary,
            description=description,
            start_time=start_dt,
            end_time=end_dt,
            location=location
        )
        
        return result
        
    except Exception as e:
        return {"error": f"Failed to create calendar event: {str(e)}"}

@mcp.tool()
def list_calendar_events(max_results: int = 10) -> Dict[str, Any]:
    """
    List upcoming events from Google Calendar.
    
    Args:
        max_results: Maximum number of events to return (default: 10)
    
    Returns:
        Dictionary with list of events or error information
    """
    try:
        calendar_service = get_calendar_service()
        if not calendar_service:
            return {"error": "Google Calendar service not available. Please check credentials."}
        
        result = calendar_service.list_events(max_results=max_results)
        return result
        
    except Exception as e:
        return {"error": f"Failed to list calendar events: {str(e)}"}

if __name__ == "__main__":
    # Run the server
    mcp.run() 