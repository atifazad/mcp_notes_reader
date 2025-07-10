#!/usr/bin/env python3
"""
Real LLM + MCP Client

A client that uses Ollama LLM to intelligently orchestrate MCP tools.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional

import click
import ollama
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

console = Console()

class MCPToolManager:
    """Manages MCP tools for LLM orchestration."""
    
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
            
            console.print("🔌 Connecting to MCP server...", style="blue")
            
            # Connect using stdio
            self._stdio_ctx = stdio_client(server_params)
            read, write = await self._stdio_ctx.__aenter__()
            
            # Create session
            self.session = ClientSession(read, write)
            await self.session.__aenter__()
            await self.session.initialize()
            
            # Discover tools
            tools_response = await self.session.list_tools()
            self.tools = tools_response.tools
            
            console.print(f"✅ Connected! Found {len(self.tools)} tools", style="green")
            return True
                    
        except Exception as e:
            console.print(f"❌ Failed to connect: {e}", style="red")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a specific tool on the server."""
        if not self.session:
            return None
        
        try:
            result = await self.session.call_tool(tool_name, arguments or {})
            return result
        except Exception as e:
            console.print(f"❌ Tool call failed: {e}", style="red")
            return None
    
    async def disconnect(self):
        """Disconnect from the server."""
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
            if self._stdio_ctx:
                await self._stdio_ctx.__aexit__(None, None, None)
        except Exception as e:
            console.print(f"⚠️  Error during disconnect: {e}", style="yellow")
    
    def get_tools_info(self) -> str:
        """Get formatted information about available tools."""
        if not self.tools:
            return "No tools available"
        
        info = "Available tools:\n"
        for tool in self.tools:
            info += f"- {tool.name}: {tool.description}\n"
            if tool.inputSchema and tool.inputSchema.get("properties"):
                params = ", ".join(tool.inputSchema["properties"].keys())
                info += f"  Parameters: {params}\n"
        return info

class OllamaLLMClient:
    """Ollama LLM client for intelligent analysis."""
    
    def __init__(self, model: str = "mistral:7b-instruct"):
        self.model = model
        self.client = ollama.Client()
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using Ollama."""
        try:
            response = self.client.chat(model=self.model, messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ])
            return response['message']['content']
        except Exception as e:
            console.print(f"❌ LLM error: {e}", style="red")
            return f"Error: {e}"
    
    def analyze_notes(self, notes_content: str, user_query: str) -> str:
        """Analyze notes content based on user query."""
        prompt = f"""You are an intelligent assistant that helps analyze notes and documents.

Available notes content:
{notes_content}

User query: {user_query}

Please provide a helpful, intelligent response based on the notes content. 
If the user is asking for specific information, extract and present it clearly.
If they want analysis or insights, provide thoughtful observations.
Be concise but thorough in your response."""
        
        return self.generate_response(prompt)
    
    def decide_tool_action(self, user_query: str, available_tools: str) -> Dict[str, Any]:
        """Decide which tool to call based on user query."""
        prompt = f"""You are an assistant that decides which tools to use based on user requests.

Available tools:
{available_tools}

User query: {user_query}

Respond with a JSON object that specifies:
1. "action": "list_notes", "read_note", or "analyze"
2. "filename": the filename to read (if applicable)
3. "reasoning": brief explanation of your decision

Example: {{"action": "read_note", "filename": "meeting.txt", "reasoning": "User wants to read meeting notes"}}

Respond only with valid JSON:"""
        
        response = self.generate_response(prompt)
        try:
            return json.loads(response)
        except:
            return {"action": "analyze", "reasoning": "Could not parse LLM response"}

class LLMOrchestrator:
    """Orchestrates LLM interactions with MCP tools."""
    
    def __init__(self, model: str = "mistral:7b-instruct"):
        self.tool_manager = MCPToolManager()
        self.llm_client = OllamaLLMClient(model)
        self.conversation_history = []
    
    async def initialize(self) -> bool:
        """Initialize the orchestrator."""
        return await self.tool_manager.connect()
    
    async def process_query(self, user_query: str) -> str:
        """Process a natural language query using real LLM intelligence."""
        
        console.print("🤖 Analyzing your request with LLM...", style="blue")
        
        # First, get available tools info
        tools_info = self.tool_manager.get_tools_info()
        
        # Let LLM decide what action to take
        decision = self.llm_client.decide_tool_action(user_query, tools_info)
        console.print(f"🔍 LLM decided: {decision.get('action', 'unknown')}", style="blue")
        
        # Execute the decided action
        if decision.get("action") == "list_notes":
            return await self._handle_list_notes()
        
        elif decision.get("action") == "read_note":
            filename = decision.get("filename")
            if filename:
                return await self._handle_read_note(filename)
            else:
                return "❌ LLM didn't specify which file to read"
        
        elif decision.get("action") == "analyze":
            return await self._handle_llm_analysis(user_query)
        
        else:
            return await self._handle_general_query(user_query)
    
    async def _handle_list_notes(self) -> str:
        """Handle requests to list notes."""
        result = await self.tool_manager.call_tool("list_notes")
        if not result or not result.content:
            return "❌ Failed to list notes"
        
        # Parse the result
        notes_info = []
        for content in result.content:
            if hasattr(content, 'text'):
                try:
                    note_data = json.loads(content.text)
                    notes_info.append(f"- {note_data['filename']} ({note_data['size']} bytes)")
                except:
                    notes_info.append(f"- {content.text}")
        
        return "📝 Available notes:\n" + "\n".join(notes_info)
    
    async def _handle_read_note(self, filename: str) -> str:
        """Handle requests to read a specific note."""
        result = await self.tool_manager.call_tool("read_note", {"filename": filename})
        if not result or not result.content:
            return f"❌ Failed to read {filename}"
        
        # Extract content
        content = result.content[0].text if result.content else "No content"
        return f"📖 Content of {filename}:\n\n{content}"
    
    async def _handle_llm_analysis(self, user_query: str) -> str:
        """Handle complex analysis requests using LLM."""
        # First, get all available notes
        result = await self.tool_manager.call_tool("list_notes")
        if not result or not result.content:
            return "❌ Failed to get notes for analysis"
        
        # Read all notes for analysis
        all_notes_content = ""
        for content in result.content:
            if hasattr(content, 'text'):
                try:
                    note_data = json.loads(content.text)
                    filename = note_data['filename']
                    
                    # Read the actual content
                    read_result = await self.tool_manager.call_tool("read_note", {"filename": filename})
                    if read_result and read_result.content:
                        note_content = read_result.content[0].text
                        all_notes_content += f"\n\n--- {filename} ---\n{note_content}"
                except:
                    continue
        
        # Let LLM analyze all notes
        return self.llm_client.analyze_notes(all_notes_content, user_query)
    
    async def _handle_general_query(self, user_query: str) -> str:
        """Handle general queries."""
        tools_info = self.tool_manager.get_tools_info()
        return f"""🤖 I can help you with your notes! Here's what I can do:

{tools_info}

Try asking me to:
- "List my notes"
- "Read meeting.txt"
- "Show me my todo list"
- "What notes do I have?"
- "Analyze my meeting notes"
- "What are my action items?"
"""
    
    async def disconnect(self):
        """Disconnect from the server."""
        await self.tool_manager.disconnect()

async def run_llm_client():
    """Main LLM client runner."""
    orchestrator = LLMOrchestrator()
    
    if not await orchestrator.initialize():
        return None
    
    return orchestrator

@click.group()
def cli():
    """Real LLM + MCP Client for intelligent note interactions."""
    pass

@cli.command()
@click.argument('query')
@click.option('--model', default='mistral:7b-instruct', help='Ollama model to use')
def ask(query, model):
    """Ask a natural language question about your notes."""
    async def _ask():
        orchestrator = LLMOrchestrator(model)
        if not await orchestrator.initialize():
            return
        
        try:
            response = await orchestrator.process_query(query)
            panel = Panel(
                Markdown(response),
                title="🤖 LLM Response",
                border_style="blue"
            )
            console.print(panel)
        finally:
            await orchestrator.disconnect()
    
    asyncio.run(_ask())

@cli.command()
@click.option('--model', default='mistral:7b-instruct', help='Ollama model to use')
def interactive(model):
    """Start interactive LLM mode."""
    async def _interactive():
        orchestrator = LLMOrchestrator(model)
        if not await orchestrator.initialize():
            return
        
        console.print(f"\n🤖 Real LLM + MCP Interactive Mode (using {model})", style="cyan")
        console.print("Ask me about your notes! Type 'quit' to exit.", style="blue")
        
        try:
            while True:
                query = input("\n> ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    continue
                
                response = await orchestrator.process_query(query)
                panel = Panel(
                    Markdown(response),
                    title="🤖 Response",
                    border_style="blue"
                )
                console.print(panel)
        
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!", style="cyan")
        finally:
            await orchestrator.disconnect()
    
    asyncio.run(_interactive())

@cli.command()
def list_tools():
    """List available tools from the server."""
    async def _list_tools():
        orchestrator = await run_llm_client()
        if orchestrator:
            orchestrator.tool_manager.display_tools()
            await orchestrator.disconnect()
    
    asyncio.run(_list_tools())

@cli.command()
def list_notes():
    """List notes from the server."""
    async def _list_notes():
        orchestrator = await run_llm_client()
        if orchestrator:
            result = await orchestrator.tool_manager.call_tool("list_notes")
            if result and result.content:
                notes_info = []
                for content in result.content:
                    if hasattr(content, 'text'):
                        try:
                            note_data = json.loads(content.text)
                            notes_info.append(f"- {note_data['filename']} ({note_data['size']} bytes)")
                        except:
                            notes_info.append(f"- {content.text}")
                
                panel = Panel(
                    "\n".join(notes_info),
                    title="📝 Available Notes",
                    border_style="green"
                )
                console.print(panel)
            await orchestrator.disconnect()
    
    asyncio.run(_list_notes())

@cli.command()
@click.argument('filename')
def read_note(filename):
    """Read a specific note from the server."""
    async def _read_note():
        orchestrator = await run_llm_client()
        if orchestrator:
            result = await orchestrator.tool_manager.call_tool("read_note", {"filename": filename})
            if result and result.content:
                content = result.content[0].text if result.content else "No content"
                panel = Panel(
                    content,
                    title=f"📖 {filename}",
                    border_style="green"
                )
                console.print(panel)
            await orchestrator.disconnect()
    
    asyncio.run(_read_note())

if __name__ == "__main__":
    cli() 