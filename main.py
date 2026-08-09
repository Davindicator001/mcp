from urllib.parse import quote
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import MCPServer

# Initialize the MCP server
mcp_server = MCPServer("free-uncensored-imagegen")


@mcp_server.tool()
async def generate_image(prompt: str) -> str:
    """Generates an image from a detailed text prompt using free cloud APIs.

    Args:
        prompt: The exact visual prompt to render.
    """
    if not prompt:
        raise ValueError("Error: Prompt was empty.")

    # URL-encode the string to protect spaces during web-routing
    encoded_prompt = quote(prompt)

    # Pull from Pollinations' image generation endpoint (default safety settings)
    image_url = f"https://pollinations.ai{encoded_prompt}?enhance=false&safe=false"

    return f"Here is your generated image:\n![Generated Image]({image_url})"


# sse_app() returns a ready-to-run Starlette app with /sse and /messages/
# routes already wired to this server instance.
app = mcp_server.sse_app()

# Enable CORS for desktop clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
