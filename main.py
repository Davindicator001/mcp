import os
import base64
import httpx
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
import mcp.types as types

# Initialize the MCP server
mcp_server = MCPServer("colab-sdxl-imagegen")

# UPDATE THIS: Use your actual ngrok URL from the cell output above
# Example: "https://deserving-reveler-daybed.ngrok-free.dev"
COLAB_URL = "https://deserving-reveler-daybed.ngrok-free.dev"

transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=["mcp-0go8.onrender.com", "localhost", "127.0.0.1"],
    allowed_origins=["*"],
)

@mcp_server.tool()
async def generate_image(prompt: str) -> types.ImageContent | str:
    """Generates an image from a detailed text prompt by calling the Colab SDXL server.

    Args:
        prompt: The exact visual prompt to render.
    """
    if not prompt:
        raise ValueError("Error: Prompt was empty.")

    # We call the /update endpoint which triggers generation and returns the file
    url = f"{COLAB_URL}/update"
    params = {"prompt": prompt}

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.get(url, params=params)
        except Exception as e:
            raise ValueError(f"Failed to connect to Colab: {str(e)}")

    if response.status_code != 200:
        raise ValueError(
            f"Colab Server error ({response.status_code}): {response.text[:300]}"
        )

    content_type = response.headers.get("content-type", "image/png")
    image_bytes = response.content
    encoded = base64.b64encode(image_bytes).decode("utf-8")

    return types.ImageContent(data=encoded, mimeType=content_type)

app = mcp_server.sse_app(transport_security=transport_security)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
