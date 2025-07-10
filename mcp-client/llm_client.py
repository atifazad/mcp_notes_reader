#!/usr/bin/env python3
"""
Real LLM + MCP Client

A client that uses Ollama LLM to intelligently orchestrate MCP tools.
"""

import asyncio
import json
import os
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
        """Decide which tool to call based on user query using true MCP auto-discovery."""
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        prompt = f"""You are an intelligent assistant that can use any available tools to help users.

IMPORTANT: Today's date is {current_date}. Use this as the reference for calculating "tomorrow", "next week", etc.

Available tools:
{available_tools}

User query: {user_query}

IMPORTANT FILE READING STRATEGY:
- When asked to read a CV, resume, or similar document, ALWAYS use list_notes first to see all available files
- Look for files with names like "cv", "resume", "curriculum vitae" (case insensitive)
- Use read_pdf for .pdf files and read_note for .txt files
- If no exact match, choose the most likely file based on the request
- NEVER use read_pdf or read_note directly for CV/resume requests - always start with list_notes

Analyze the user's request and respond with a JSON object that specifies:
1. "tool_name": The exact name of the tool to call (must match one of the available tools)
2. "arguments": A dictionary of arguments to pass to the tool
3. "reasoning": Brief explanation of why you chose this tool and these arguments

For date calculations:
- "tomorrow" = {current_date} + 1 day
- "next week" = {current_date} + 7 days
- Use ISO format: YYYY-MM-DDTHH:MM:SS

Examples:
- {{"tool_name": "read_note", "arguments": {{"filename": "meeting.txt"}}, "reasoning": "User wants to read meeting notes"}}
- {{"tool_name": "read_pdf", "arguments": {{"filename": "cv.pdf"}}, "reasoning": "User wants to read their CV, found PDF file"}}
- {{"tool_name": "list_calendar_events", "arguments": {{"max_results": 5}}, "reasoning": "User wants to see upcoming events"}}
- {{"tool_name": "create_calendar_event", "arguments": {{"summary": "Team Meeting", "description": "Weekly team sync", "start_time": "2025-07-12T14:00:00", "end_time": "2025-07-12T15:00:00", "location": "Conference Room A"}}, "reasoning": "User wants to create a calendar event for tomorrow"}}

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
    
    async def initialize(self) -> bool:
        """Initialize the orchestrator."""
        return await self.tool_manager.connect()
    
    async def process_query(self, user_query: str) -> str:
        """Process a natural language query using real LLM intelligence with true MCP auto-discovery."""
        
        # Check for meta-questions about tools/capabilities
        meta_keywords = [
            "what tools", "available tools", "list tools", "what can you do", "your capabilities", "show tools", "tool list"
        ]
        if any(kw in user_query.lower() for kw in meta_keywords):
            tools_info = self.tool_manager.get_tools_info()
            return f"🛠️ Here are the available tools:\n\n{tools_info}"
        
        console.print("🤖 Analyzing your request with LLM...", style="blue")
        
        # First, get available tools info
        tools_info = self.tool_manager.get_tools_info()
        
        # Let LLM decide which tool to use (true MCP auto-discovery)
        decision = self.llm_client.decide_tool_action(user_query, tools_info)
        console.print(f"🔍 LLM decided: {decision.get('tool_name', 'unknown')}", style="blue")
        console.print(f"💭 Reasoning: {decision.get('reasoning', 'No reasoning provided')}", style="blue")
        
        # Execute the tool call using true MCP auto-discovery
        tool_name = decision.get("tool_name")
        arguments = decision.get("arguments", {})
        
        if tool_name:
            # Call the tool directly - this is true MCP auto-discovery!
            result = await self.tool_manager.call_tool(tool_name, arguments)
            if result and result.content:
                # Aggregate all content items for list_notes
                if tool_name == "list_notes":
                    # Join all content items as a JSON array if possible
                    try:
                        # If each content item is a JSON object, join them into a list
                        all_json = [json.loads(c.text) for c in result.content if hasattr(c, 'text')]
                        # Flatten if already a list (for backward compatibility)
                        if all_json and isinstance(all_json[0], list):
                            all_json = [item for sublist in all_json for item in sublist]
                        content = json.dumps(all_json)
                    except Exception as e:
                        content = "\n".join([c.text for c in result.content if hasattr(c, 'text')])
                    
                    # Check if this was a CV/resume request and we need to find the right file
                    cv_keywords = ['cv', 'resume', 'curriculum vitae', 'skills', 'experience']
                    if any(keyword in user_query.lower() for keyword in cv_keywords):
                        # Let the LLM choose the right file from the list
                        cv_response = await self._handle_cv_request(user_query, content)
                        if cv_response:
                            return cv_response
                    
                    return await self._format_notes_list(content)
                else:
                    content = result.content[0].text if result.content else "No content"
                    if tool_name == "read_note":
                        return f"📖 Content of {arguments.get('filename', 'file')}:\n\n{content}"
                    elif tool_name == "read_pdf":
                        return f"📄 Content of {arguments.get('filename', 'PDF')}:\n\n{content}"
                    elif tool_name == "list_calendar_events":
                        return await self._format_calendar_events(content)
                    elif tool_name == "create_calendar_event":
                        return await self._format_calendar_creation(content, arguments.get('summary', 'Event'))
                    else:
                        return f"✅ Tool '{tool_name}' executed successfully:\n\n{content}"
            else:
                return f"❌ Failed to execute tool '{tool_name}'"
        else:
            return await self._handle_general_query(user_query)
    
    async def _format_notes_list(self, content: str) -> str:
        """Format the list notes response."""
        try:
            note_data = json.loads(content)
            notes_info = []
            for note in note_data:
                notes_info.append(f"- {note['filename']} ({note['size']} bytes)")
            return "📝 Available notes:\n" + "\n".join(notes_info)
        except Exception as e:
            # Debug: print the content to see what we're getting
            console.print(f"Debug: Failed to parse JSON: {e}", style="yellow")
            console.print(f"Debug: Content: {content}", style="yellow")
            return f"📝 Available notes:\n\n{content}"
    
    def extract_event_date(self, event):
        # Handle complete start/end objects from Google Calendar API
        start = event.get('start', {})
        end = event.get('end', {})
        
        # Check for dateTime (timed events) first
        if 'dateTime' in start:
            return start['dateTime']
        if 'dateTime' in end:
            return end['dateTime']
        
        # Check for date (all-day events)
        if 'date' in start:
            return start['date']
        if 'date' in end:
            return end['date']
        
        # Fallback: try to extract from event ID
        event_id = event.get("id", "")
        if "_" in event_id:
            date_part = event_id.split("_")[-1]
            if len(date_part) == 8:
                return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
        return "date not specified"

    async def _format_calendar_events(self, content: str) -> str:
        """Format the calendar events response."""
        try:
            data = json.loads(content)
            if data.get("success") and data.get("events"):
                events_info = []
                for event in data["events"]:
                    summary = event.get("summary", "Untitled")
                    location = event.get("location", "")
                    date_str = self.extract_event_date(event)
                    if 'T' in date_str:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            time_display = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            time_display = date_str
                    elif date_str != "date not specified":
                        time_display = f"All-day event on {date_str}"
                    else:
                        time_display = "All-day event (date not specified)"
                    events_info.append(f"📅 **{summary}**\n   📍 {location}\n   🕐 {time_display}")
                return f"📅 Upcoming Calendar Events:\n\n" + "\n\n".join(events_info)
            else:
                return f"📅 Calendar Events:\n\n{content}"
        except:
            return f"📅 Calendar Events:\n\n{content}"
    
    async def _format_calendar_creation(self, content: str, summary: str) -> str:
        """Format the calendar event creation response."""
        try:
            data = json.loads(content)
            if data.get("success"):
                event_id = data.get("event_id", "Unknown")
                html_link = data.get("html_link", "")
                return f"✅ Calendar event created successfully!\n\n📅 **{summary}**\n🔗 {html_link}\n🆔 Event ID: {event_id}"
            else:
                error = data.get("error", "Unknown error")
                return f"❌ Failed to create calendar event: {error}"
        except:
            return f"📅 Calendar Event Creation Result:\n\n{content}"
    
    async def _handle_cv_request(self, user_query: str, files_content: str) -> str:
        """Handle CV/resume requests by intelligently selecting the right file."""
        try:
            # Parse the files list
            files_data = json.loads(files_content)
            
            # Let LLM choose the best CV file
            prompt = f"""You are helping to find the user's CV/resume file.

Available files:
{files_content}

User request: {user_query}

Based on the user's request and the available files, choose the most likely CV/resume file.
Look for files with names containing: cv, resume, curriculum vitae, etc.

Respond with a JSON object:
{{"filename": "exact_filename_with_extension", "reasoning": "why you chose this file"}}

Examples:
- If user asks for CV and you see "*cv*.pdf", choose that
- If user asks for resume and you see "resume.txt", choose that
- If no clear CV file, choose the most likely one

Respond only with valid JSON:"""
            
            response = self.llm_client.generate_response(prompt)
            try:
                decision = json.loads(response)
                filename = decision.get("filename")
                reasoning = decision.get("reasoning", "No reasoning provided")
                
                if filename:
                    # Determine the correct tool to use
                    if filename.endswith('.pdf'):
                        tool_name = "read_pdf"
                    else:
                        tool_name = "read_note"
                    
                    # Read the selected file
                    result = await self.tool_manager.call_tool(tool_name, {"filename": filename})
                    if result and result.content:
                        content = result.content[0].text if result.content else "No content"
                        
                        # Use LLM to analyze the CV content and provide summary
                        analysis_prompt = f"""You are an expert at analyzing CVs and resumes. 

CV Content:
{content}

User Request: {user_query}

Please provide a comprehensive analysis and summary based on the user's request. Focus on:
- Key skills and technologies
- Work experience highlights
- Notable projects and achievements
- Education and qualifications
- Any specific areas the user asked about

Provide a well-structured, professional summary."""
                        
                        analysis = self.llm_client.generate_response(analysis_prompt)
                        return f"📄 **CV Analysis** (chose {filename} based on: {reasoning})\n\n{analysis}"
                    else:
                        return f"❌ Failed to read {filename}"
                else:
                    return f"❌ Could not determine which file is your CV. Available files:\n\n{files_content}"
            
            except json.JSONDecodeError:
                return f"❌ Could not parse LLM response for CV selection. Available files:\n\n{files_content}"
        
        except Exception as e:
            return f"❌ Error handling CV request: {e}\n\nAvailable files:\n\n{files_content}"
    

    

    
    async def _handle_general_query(self, user_query: str) -> str:
        """Handle general queries."""
        tools_info = self.tool_manager.get_tools_info()
        return f"""🤖 I can help you with your notes and calendar! Here's what I can do:

{tools_info}

Try asking me to:
- "List my notes"
- "Read meeting.txt"
- "Analyze my CV and summarise it"
- "Show me my todo list"
- "What notes do I have?"
- "Analyze my meeting notes"
- "What are my action items?"
- "Show my upcoming calendar events"
- "Create a meeting for tomorrow at 2pm"
- "Schedule a team meeting next week"
- "What's on my calendar this week?"
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
            tools_info = orchestrator.tool_manager.get_tools_info()
            panel = Panel(
                tools_info,
                title="🛠️ Available Tools",
                border_style="green"
            )
            console.print(panel)
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