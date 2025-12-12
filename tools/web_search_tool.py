from dotenv import load_dotenv
from langchain.tools import tool
import requests
import os


load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")


@tool
async def web_search(query: str, num_results: int = 5) -> str:
    """Perform a web search and return consolidated text with top result facts."""
    print(f"Performing web search for query: {query} with top {num_results} results.")
    response = requests.get(
        "https://serpapi.com/search.json",
        params={
            "engine": "google",
            "q": query,
            "api_key": SERP_API_KEY,
        },
    )
    response.raise_for_status()
    data = response.json()

    organic_results = data.get("organic_results", [])

    fact_chunks = []

    for result in organic_results[:num_results]:
        title = (result.get("title") or "").strip()
        snippet = (result.get("snippet") or "").strip()
        link = (result.get("link") or "").strip()

        print(f"Title: {title}\nSnippet: {snippet}\nLink: {link}\n")

        # Skip empty ones
        if not (title or snippet):
            continue

        chunk_lines = []
        if title:
            chunk_lines.append(f"Title: {title}")
        if snippet:
            chunk_lines.append(f"Summary: {snippet}")
        if link:
            chunk_lines.append(f"Source: {link}")

        fact_chunks.append("\n".join(chunk_lines))

    # This final string is what you pass into the Researcher agent output
    consolidated_text = "\n\n".join(fact_chunks)
    return consolidated_text
