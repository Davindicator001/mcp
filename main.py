import os
import base64
import httpx
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
import mcp.types as types

# Initialize the MCP server
mcp_server = MCPServer("free-uncensored-imagegen")

HF_TOKEN = os.environ.get("HF_TOKEN")
 
HF_MODEL = "John6666/spicy-realism-nsfw-mix-v30-sdxl"
# Hugging Face deprecated api-inference.huggingface.co in favor of the new
# router. The old hostname no longer resolves at all (hence "No address
# associated with hostname" errors) — this is the current endpoint format.
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}"
 
# The SSE transport validates the Host header by default (DNS-rebinding
# protection) and rejects any host not in this list. Add your Render
# domain here, or requests will fail with "Request validation failed".
transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=["mcp-0go8.onrender.com", "localhost", "127.0.0.1"],
    allowed_origins=["*"],
)
 
 
@mcp_server.tool()
async def generate_image(prompt: str) -> types.ImageContent | str:
    """Generates an image from a detailed text prompt using the Hugging Face
    Inference API (John6666/spicy-realism-nsfw-mix-v30-sdxl).
 
    Args:
        prompt: The exact visual prompt to render.
    """
    if not prompt:
        raise ValueError("Error: Prompt was empty.")
 
    if not HF_TOKEN:
        raise ValueError(
            "Server misconfiguration: HF_TOKEN environment variable is not set."
        )
 
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
 
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            HF_API_URL,
            headers=headers,
            json={"inputs": prompt},
        )
 
    # The free Inference API returns 503 while the model is "cold" and
    # spinning up on HF's shared infra — this is normal, not a bug.
    if response.status_code == 503:
        raise ValueError(
            "The model is still loading on Hugging Face's servers. "
            "Please try again in 20-30 seconds."
        )
 
    if response.status_code != 200:
        raise ValueError(
            f"Hugging Face API error ({response.status_code}): {response.text[:300]}"
        )
 
    content_type = response.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        # HF returns JSON on errors (e.g. bad token, rate limit) instead of image bytes
        raise ValueError(f"Unexpected response from Hugging Face: {response.text[:300]}")
 
    image_bytes = response.content
    encoded = base64.b64encode(image_bytes).decode("utf-8")
 
    return types.ImageContent(data=encoded, mimeType=content_type)
 
 
# sse_app() returns a ready-to-run Starlette app with /sse and /messages/
# routes already wired to this server instance.
app = mcp_server.sse_app(transport_security=transport_security)
 
# Enable CORS for desktop clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
