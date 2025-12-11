import os
import asyncio
import logging
from fastmcp import Client
from dotenv import load_dotenv

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

_cached_mcp_tools = None
_tools_fetch_error = False

logging.getLogger("asyncio").setLevel(logging.ERROR)


async def get_mcp_tools_for_openai(force_refresh: bool = False):
    global _cached_mcp_tools, _tools_fetch_error
    
    if _cached_mcp_tools is not None and not force_refresh:
        return _cached_mcp_tools
    
    if not MCP_SERVER_URL:
        return []
    
    try:
        async with Client(MCP_SERVER_URL) as mcp_client:
            tools = await mcp_client.list_tools()
            openai_tools = []
            for tool in tools:
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or f"Tool: {tool.name}",
                        "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') and tool.inputSchema else {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
                openai_tools.append(openai_tool)
            
            _cached_mcp_tools = openai_tools
            _tools_fetch_error = False

            return openai_tools

    except (ConnectionError, ConnectionResetError, OSError) as e:
        _tools_fetch_error = True
        return _cached_mcp_tools if _cached_mcp_tools is not None else []

    except Exception:
        _tools_fetch_error = True
        return _cached_mcp_tools if _cached_mcp_tools is not None else []


async def execute_mcp_tool(tool_name: str, parameters: dict):
    if not MCP_SERVER_URL:
        return f"Error: MCP server not configured. Cannot call tool {tool_name}"
    
    try:
        async with Client(MCP_SERVER_URL) as mcp_client:
            result = await mcp_client.call_tool(tool_name, parameters)
            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return f"Tool {tool_name} returned empty result"

    except (ConnectionError, ConnectionResetError, OSError) as e:
        return f"Error: Could not connect to MCP server. {str(e)}"

    except Exception as e:
        return f"Error calling tool {tool_name}: {str(e)}"

