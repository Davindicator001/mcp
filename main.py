import os
import asyncio
from urllib.parse import quote
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from mcp.server import Server
from mcp.server.sse import SseServerTransport
import mcp.types as types

# Initialize FastAPI app and MCP Server
app = FastAPI(title="Free Uncensored ImageGen Server")
mcp_server = Server("free-uncensored-imagegen")
sse_transport = SseServerTransport("/messages")

# Define the image generation tool
@mcp_server.list_tools()
async def handle_list_tools():
    return [
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

@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name != "generate_image":
        raise ValueError(f"Unknown tool: {name}")
    
    prompt = arguments.get("prompt")
    if not prompt:
        return [types.TextContent(type="text", text="Error: Prompt is empty.")]

    try:
        # URL-encode the prompt string to handle spaces and special characters safely
        encoded_prompt = quote(prompt)
        
        # Build the Pollinations URL with safety filters explicitly turned off
        # "safe=false" requests the unaligned backend model pipelines
        image_url = f"https://pollinations.ai{encoded_prompt}?enhance=false&safe=false"
        
        # Return Markdown to instantly render the image inside your local chat UI
        return [
            types.TextContent(
                type="text", 
                text=f"Here is your generated image:\n![Generated Image]({image_url})"
            )
        ]
            
    except Exception as e:
        return [types.TextContent(type="text", text=f"An error occurred: {str(e)}")]

# MCP SSE Transport Routes
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
