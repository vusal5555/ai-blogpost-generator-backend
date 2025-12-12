from dotenv import load_dotenv
from typing import Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict, Optional
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


llm = init_chat_model("claude-sonnet-4-5-20250929")

llm.bind_tools([web_search])


class State(TypedDict):
    messages: Annotated[list, add_messages]
    research_notes: Optional[str]
    draft: Optional[str]
    fact_check_passed: Optional[bool]
    fact_check_issues: Optional[str]
    final_post: Optional[str]
    retry_count: int


graph_builder = StateGraph(State)


def research_agent(state: State):
    print("Research Agent Invoked")
    last_message = state["messages"][-1]

    messages = [
        {
            "role": "system",
            "content": """You are a research agent. Your task is to help users by providing well-researched and accurate information based on their queries. Use reliable sources and ensure that your responses are clear and concise.""",
        },
        {"role": "user", "content": last_message.content},
    ]

    reply = llm.invoke(messages)
    return {
        "research_notes": reply.content,
        "messages": [{"role": "assistant", "content": reply.content}],
    }


def writer_agent(state: State):
    print("Writer Agent Invoked")
    last_message = state["messages"][-1]
    research = state.get("research_notes", "")
    issues = state.get("fact_check_issues", "")
    draft = state.get("draft", "")
    if issues:
        messages = [
            {
                "role": "system",
                "content": f"""Revise the draft to fix these fact-check issues:\n{issues}\n\n"
                "Here’s the original draft:"
                {draft}

            "Here’s the original draftissues in your writing:
            {issues}
            """,
            },
            {"role": "user", "content": last_message.content},
        ]
        research += f"\n\nPlease address the following issues found during fact-checking:\n{issues}"
    messages = [
        {
            "role": "system",
            "content": f"""You are a content writer. Your task is to create engaging and informative articles based on the research notes provided. Ensure that the content is well-structured, easy to read, and free of plagiarism. 
            
            Use the research notes to back up your statements and provide value to the reader.
            {research}
            """,
        },
        {"role": "user", "content": last_message.content},
    ]

    reply = llm.invoke(messages)
    return {
        "draft": reply.content,
        "messages": [{"role": "assistant", "content": reply.content}],
    }


def fact_check_router(state: State) -> Literal["polisher_agent", "writer_agent"]:
    print("Fact Check Router Invoked")
    if state.get("fact_check_passed"):
        return "polisher_agent"
    if state.get("retry_count", 0) >= 2:
        return "polisher_agent"
    return "writer_agent"


def fact_checker_agent(state: State):
    draft = state.get("draft", "")
    research_notes = state.get("research_notes", "")
    retry_count = state.get("retry_count", 0)

    print("Fact Checker Agent Invoked")

    messages = [
        {
            "role": "system",
            "content": """You are a fact-checking agent. Your task is to verify the accuracy of the information presented in the draft based on the provided research notes. Ensure that all facts, figures, and statements are supported by credible sources. If you find any discrepancies or inaccuracies, highlight them and suggest corrections.""",
        },
        {
            "role": "user",
            "content": f"""Draft:{draft}           
        
            Research Notes:
            {research_notes}
            """,
        },
    ]

    reply = llm.invoke(messages)
    issues = reply.content.strip()
    if len(issues) == 0:
        return {
            "fact_check_passed": True,
            "messages": [
                {"role": "assistant", "content": "Fact check passed with no issues."}
            ],
        }
    else:
        return {
            "fact_check_passed": False,
            "fact_check_issues": issues,
            "retry_count": retry_count + 1,
            "messages": [{"role": "assistant", "content": issues}],
        }


def polisher_agent(state: State):
    print("Polisher Agent Invoked")
    draft = state.get("draft", "")
    messages = [
        {
            "role": "system",
            "content": """You are a content polishing agent. Your task is to refine and enhance the draft to ensure it is polished, coherent, and engaging. Focus on improving grammar, style, and overall readability while maintaining the original message and intent of the content. Ensure that the final output is professional and ready for publication. make sure that all the extra charachers are removed such as special charachers etc.""",
        },
        {"role": "user", "content": draft},
    ]

    reply = llm.invoke(messages)
    return {
        "final_post": reply.content,
        "messages": [{"role": "assistant", "content": reply.content}],
    }


graph_builder.add_node(
    "research_agent",
    research_agent,
)
graph_builder.add_node(
    "writer_agent",
    writer_agent,
)


graph_builder.add_node(
    "fact_checker_agent",
    fact_checker_agent,
)

graph_builder.add_node(
    "polisher_agent",
    polisher_agent,
)


graph_builder.add_edge(START, "research_agent")

graph_builder.add_edge("research_agent", "writer_agent")
graph_builder.add_edge("writer_agent", "fact_checker_agent")
graph_builder.add_conditional_edges("fact_checker_agent", fact_check_router)
graph_builder.add_edge("polisher_agent", END)


orchestrater = graph_builder.compile()


state = orchestrater.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "What are the latest advancements in renewable energy?",
            }
        ],
        "retry_count": 0,
    }
)

print(state.get("final_post", "No final post generated"))
