#!/usr/bin/env python3
"""
Simple MCP Client - Stdio Version

A basic MCP client for testing and interacting with MCP servers using stdio transport.
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

console = Console()

class MCPClient:
    """Simple MCP client for testing servers using stdio transport."""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.tools: List[Dict[str, Any]] = []
        self._stdio_ctx = None
        
    async def connect(self) -> bool:
        """Connect to the MCP server via stdio."""
        try:
            # Get the correct path to server.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            server_path = os.path.join(current_dir, "..", "server.py")
            
            # Configure server parameters
            server_params = StdioServerParameters(
                command="python",
                args=[server_path],
                cwd=os.path.join(current_dir, "..")
            )
            
            console.print(f"🔌 Connecting to MCP server via stdio at {server_path}...", style="blue")
            
            # Connect using stdio
            self._stdio_ctx = stdio_client(server_params)
            read, write = await self._stdio_ctx.__aenter__()
            console.print("✅ Connected to server via stdio!", style="green")
            
            # Create session
            self.session = ClientSession(read, write)
            await self.session.__aenter__()
            console.print("✅ Created MCP session!", style="green")
            
            # Initialize
            await self.session.initialize()
            console.print("✅ Session initialized!", style="green")
            return True
                    
        except Exception as e:
            console.print(f"❌ Failed to connect: {e}", style="red")
            return False
    
    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover available tools from the server."""
        if not self.session:
            console.print("❌ Not connected to server", style="red")
            return []
        
        try:
            console.print("🔍 Discovering tools...", style="blue")
            
            # List available tools
            tools_response = await self.session.list_tools()
            self.tools = tools_response.tools
            
            console.print(f"✅ Found {len(self.tools)} tools", style="green")
            return self.tools
            
        except Exception as e:
            console.print(f"❌ Failed to discover tools: {e}", style="red")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a specific tool on the server."""
        if not self.session:
            console.print("❌ Not connected to server", style="red")
            return None
        
        try:
            console.print(f"🛠️  Calling tool: {tool_name}", style="blue")
            
            # Call the tool
            result = await self.session.call_tool(tool_name, arguments or {})
            
            console.print(f"✅ Tool {tool_name} executed successfully", style="green")
            return result
            
        except Exception as e:
            console.print(f"❌ Failed to call tool {tool_name}: {e}", style="red")
            return None
    
    async def disconnect(self):
        """Disconnect from the server."""
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
            if self._stdio_ctx:
                await self._stdio_ctx.__aexit__(None, None, None)
            console.print("🔌 Disconnected from server", style="blue")
        except Exception as e:
            console.print(f"⚠️  Error during disconnect: {e}", style="yellow")
    
    def display_tools(self):
        """Display available tools in a table."""
        if not self.tools:
            console.print("❌ No tools available", style="red")
            return
        
        table = Table(title="Available Tools")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Parameters", style="yellow")
        
        for tool in self.tools:
            params = ", ".join(tool.inputSchema.get("properties", {}).keys()) if tool.inputSchema else "None"
            table.add_row(
                tool.name,
                tool.description or "No description",
                params
            )
        
        console.print(table)
    
    def display_result(self, result: Any, tool_name: str):
        """Display tool result in a formatted way."""
        if result is None:
            console.print("❌ No result received", style="red")
            return
        
        # Handle TextContent objects
        if hasattr(result, 'content'):
            content = result.content
        else:
            content = result
        
        # Create a panel for the result
        if isinstance(content, (dict, list)):
            try:
                display_content = json.dumps(content, indent=2)
            except TypeError:
                display_content = str(content)
        else:
            display_content = str(content)
        
        panel = Panel(
            display_content,
            title=f"Result from {tool_name}",
            border_style="green"
        )
        console.print(panel)

async def run_client():
    """Main client runner."""
    client = MCPClient()
    
    try:
        # Connect to server
        if not await client.connect():
            return None
        
        # Discover tools
        await client.discover_tools()
        
        # Display tools
        client.display_tools()
        
        # Keep connection open for interactive mode
        return client
        
    except Exception as e:
        console.print(f"❌ Client error: {e}", style="red")
        return None

@click.group()
def cli():
    """Simple MCP Client for testing servers."""
    pass

@cli.command()
def list_tools():
    """List available tools from the server."""
    async def _list_tools():
        client = await run_client()
        if client:
            await client.disconnect()
    
    asyncio.run(_list_tools())

@cli.command()
def list_notes():
    """List notes from the server."""
    async def _list_notes():
        client = await run_client()
        if client:
            result = await client.call_tool("list_notes")
            client.display_result(result, "list_notes")
            await client.disconnect()
    
    asyncio.run(_list_notes())

@cli.command()
@click.argument('filename')
def read_note(filename):
    """Read a specific note from the server."""
    async def _read_note():
        client = await run_client()
        if client:
            result = await client.call_tool("read_note", {"filename": filename})
            client.display_result(result, "read_note")
            await client.disconnect()
    
    asyncio.run(_read_note())

@cli.command()
@click.argument('filename')
def read_pdf(filename):
    """Read a specific PDF file from the server."""
    async def _read_pdf():
        client = await run_client()
        if client:
            result = await client.call_tool("read_pdf", {"filename": filename})
            client.display_result(result, "read_pdf")
            await client.disconnect()
    
    asyncio.run(_read_pdf())

@cli.command()
@click.option('--max_results', default=10, help='Maximum number of events to return')
def list_calendar_events(max_results):
    """List upcoming events from Google Calendar."""
    async def _list_calendar_events():
        client = await run_client()
        if client:
            result = await client.call_tool("list_calendar_events", {"max_results": max_results})
            client.display_result(result, "list_calendar_events")
            await client.disconnect()
    
    asyncio.run(_list_calendar_events())

@cli.command()
@click.argument('summary')
@click.option('--description', default='', help='Event description')
@click.option('--start_time', default='', help='Start time in ISO format (e.g., "2024-01-15T14:00:00")')
@click.option('--end_time', default='', help='End time in ISO format')
@click.option('--location', default='', help='Event location')
def create_calendar_event(summary, description, start_time, end_time, location):
    """Create an event in Google Calendar."""
    async def _create_calendar_event():
        client = await run_client()
        if client:
            arguments = {
                "summary": summary,
                "description": description,
                "start_time": start_time,
                "end_time": end_time,
                "location": location
            }
            result = await client.call_tool("create_calendar_event", arguments)
            client.display_result(result, "create_calendar_event")
            await client.disconnect()
    
    asyncio.run(_create_calendar_event())

@cli.command()
def interactive():
    """Start interactive mode."""
    async def _interactive():
        client = await run_client()
        if not client:
            return
        
        console.print("\n🎮 Interactive mode - Type 'help' for commands, 'quit' to exit", style="cyan")
        
        try:
            while True:
                command = input("\n> ").strip().lower()
                
                if command == 'quit' or command == 'exit':
                    break
                elif command == 'help':
                    console.print("""
Available commands:
- list_notes: List all available notes
- read_note <filename>: Read a specific note
- read_pdf <filename>: Read a specific PDF file
- list_calendar_events [max_results]: List upcoming calendar events
- create_calendar_event <summary> [options]: Create a calendar event
- tools: Show available tools
- quit/exit: Exit interactive mode
                    """, style="blue")
                elif command == 'list_notes':
                    result = await client.call_tool("list_notes")
                    client.display_result(result, "list_notes")
                elif command.startswith('read_note '):
                    filename = command.split(' ', 1)[1]
                    result = await client.call_tool("read_note", {"filename": filename})
                    client.display_result(result, "read_note")
                elif command.startswith('read_pdf '):
                    filename = command.split(' ', 1)[1]
                    result = await client.call_tool("read_pdf", {"filename": filename})
                    client.display_result(result, "read_pdf")
                elif command.startswith('list_calendar_events'):
                    parts = command.split(' ')
                    max_results = int(parts[1]) if len(parts) > 1 else 10
                    result = await client.call_tool("list_calendar_events", {"max_results": max_results})
                    client.display_result(result, "list_calendar_events")
                elif command.startswith('create_calendar_event '):
                    parts = command.split(' ', 1)
                    if len(parts) < 2:
                        console.print("❌ Usage: create_calendar_event <summary> [description] [start_time] [end_time] [location]", style="red")
                        continue
                    summary = parts[1]
                    # For simplicity, we'll just use the summary for now
                    result = await client.call_tool("create_calendar_event", {"summary": summary})
                    client.display_result(result, "create_calendar_event")
                elif command == 'tools':
                    client.display_tools()
                else:
                    console.print("❌ Unknown command. Type 'help' for available commands.", style="red")
        
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!", style="cyan")
        finally:
            await client.disconnect()
    
    asyncio.run(_interactive())

if __name__ == "__main__":
    cli() 