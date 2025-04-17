from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
import json
import os
from bs4 import BeautifulSoup
from config import DOCS_CONFIG

load_dotenv()

mcp = FastMCP("docs")

USER_AGENT = "docs-app/1.0"
SERPER_URL="https://google.serper.dev/search"

async def search_web(query: str) -> dict | None:
    payload = json.dumps({"q": query, "num": 2})

    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                SERPER_URL, headers=headers, data=payload, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"organic": []}
  
async def fetch_url(url: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=30.0)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
            return text
        except httpx.TimeoutException:
            return "Timeout error"

def get_supported_libraries():
    """Returns a formatted string of supported libraries and their descriptions."""
    return "\n".join([f"- {lib}: {info['description']}" for lib, info in DOCS_CONFIG.items()])

@mcp.tool()  
async def get_docs(query: str, library: str):
    """
    Search the latest docs for a given query and library.
    
    Supported libraries:
    {supported_libraries}

    Args:
        query: The query to search for (e.g. "Chroma DB")
        library: The library to search in (e.g. "langchain")

    Returns:
        Text from the docs
    """
    if library not in DOCS_CONFIG:
        raise ValueError(f"Library {library} not supported by this tool. Supported libraries: {', '.join(DOCS_CONFIG.keys())}")
    
    query = f"site:{DOCS_CONFIG[library]['url']} {query}"
    results = await search_web(query)
    if len(results["organic"]) == 0:
        return "No results found"
    
    text = ""
    for result in results["organic"]:
        text += await fetch_url(result["link"])
    return text

# Update the docstring with supported libraries
get_docs.__doc__ = get_docs.__doc__.format(supported_libraries=get_supported_libraries())

if __name__ == "__main__":
    mcp.run(transport="stdio")