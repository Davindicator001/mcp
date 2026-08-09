import os
from urllib.parse import quote
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from mcp.server.fastapi import FastApiServer
from mcp.shared.exceptions import McpError
import mcp.types as types

# Initialize the Base MCP Server instance
mcp_server = FastApiServer(name="free-uncensored-imagegen", version="1.0.0")

# Define the image generation tool using the correct SDK decorator syntax
@mcp_server.tool(
    name="generate_image",
    description="Generates an image from a detailed text prompt using free cloud APIs."
)
async def generate_image(prompt: str) -> list[types.TextContent]:
    if not prompt:
        raise McpError(types.INVALID_PARAMS, "Prompt cannot be empty.")

    try:
        # URL-encode the prompt string to handle spaces safely
        encoded_prompt = quote(prompt)
        
        # Build the Pollinations URL with safety filters explicitly turned off
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

# Initialize FastAPI application
app = FastAPI(title="Free Uncensored ImageGen Server")

# Mount the MCP server directly into FastAPI
# This automatically handles the SSE endpoints under the hood
mcp_server.mount(app)

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")
