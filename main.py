import os
import asyncio
from urllib.parse import quote
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.server.sse import SseServerTransport
import mcp.types as types

# Initialize the low-level base MCP Server 
mcp_server = Server("free-uncensored-imagegen")

# FIX: SseServerTransport MUST be a relative path string
sse_transport = SseServerTransport("/messages")

# Register the available tools list
async def on_list_tools(params) -> types.ListToolsResult:
    return types.ListToolsResult(
        tools=[
            types.Tool(
                name="generate_image",
                description="Generates an image from a detailed text prompt using free cloud APIs.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "The exact visual prompt to render."}
                    },
                    "required": ["prompt"]
                }
            )
        ]
    )

# Handle runtime client tool execution requests
async def on_call_tool(name: str, arguments: dict | None) -> types.CallToolResult:
    if name != "generate_image":
        return types.CallToolResult(
            isError=True, 
            content=[types.TextContent(type="text", text=f"Unknown tool: {name}")]
        )
    
    if not arguments or "prompt" not in arguments:
        return types.CallToolResult(
            isError=True, 
            content=[types.TextContent(type="text", text="Error: Prompt was empty.")]
        )
        
    prompt = arguments["prompt"]

    try:
        # URL-encode the string to protect spaces during web-routing
        encoded_prompt = quote(prompt)
        
        # Pull directly from Pollinations' open image pipeline with content checks bypassed
        image_url = f"https://pollinations.ai{encoded_prompt}?enhance=false&safe=false"
        
        # Return Markdown schema syntax to natively display the image in your client's window
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text", 
                    text=f"Here is your generated image:\n![Generated Image]({image_url})"
                )
            ]
        )
            
    except Exception as e:
        return types.CallToolResult(
            isError=True, 
            content=[types.TextContent(type="text", text=f"An error occurred: {str(e)}")]
        )

# Attach mapped functions to the server instance
mcp_server.list_tools_handler = on_list_tools
mcp_server.call_tool_handler = on_call_tool

# Initialize FastAPI application container
app = FastAPI(title="Free Uncensored ImageGen Server")

# CRITICAL FIX FOR DESKTOP CLIENTS: Enable full CORS permissions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handle standard Server-Sent Events (SSE) lifecycles
@app.get("/sse")
async def sse_endpoint(request: Request):
    async with sse_transport.connect_scope(request) as scope:
        await mcp_server.run(
            scope.read_stream,
            scope.write_stream,
            mcp_server.create_initialization_options()
        )

@app.post("/messages")
async def messages_endpoint(request: Request):
    await sse_transport.handle_post_request(request)

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")
