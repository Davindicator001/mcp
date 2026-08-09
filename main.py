import os
from urllib.parse import quote
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from mcp.server.fastmcp import FastMCP
import mcp.types as types

# Initialize FastMCP - This automatically sets up a FastAPI sub-app and tools
mcp_server = FastMCP(
    name="free-uncensored-imagegen",
    title="Free Uncensored Image Generator"
)

# Define your image generation tool using the decorator
@mcp_server.tool(
    name="generate_image",
    description="Generates an image from a detailed text prompt using free cloud APIs."
)
async def generate_image(prompt: str) -> str:
    if not prompt:
        return "Error: Prompt cannot be empty."

    try:
        # URL-encode the prompt string to handle spaces safely
        encoded_prompt = quote(prompt)
        
        # Build the Pollinations URL with safety filters turned off
        image_url = f"https://pollinations.ai{encoded_prompt}?enhance=false&safe=false"
        
        # Return Markdown to instantly render the image inside your local chat UI
        return f"Here is your generated image:\n![Generated Image]({image_url})"
            
    except Exception as e:
        return f"An error occurred: {str(e)}"

# Create your main FastAPI application
app = FastAPI(title="Main API Entrypoint")

# Mount the MCP server's application instance directly into your main FastAPI app
# This makes it available over HTTP/SSE
app.mount("/mcp", mcp_server.fastapi_app)

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")
