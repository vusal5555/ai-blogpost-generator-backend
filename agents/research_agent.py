from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from agents.state import State
import os
from supabase import create_client
import uuid

from tools.web_search_tool import web_search


load_dotenv()

supabase = create_client(
    os.getenv("PUBLIC_SUPABASE_URL"),
    os.getenv("PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY"),
)


llm = init_chat_model("claude-sonnet-4-5-20250929")

llm_with_tools = llm.bind_tools([web_search])


def research_agent(state: State):
    print("Research Agent Invoked")
    run_id = state.get("run_id") or str(uuid.uuid4())
    last_message = state["messages"][-1]
    message_content = (
        last_message.content
        if hasattr(last_message, "content")
        else last_message["content"]
    )

    messages = [
        {
            "role": "system",
            "content": """You are a research agent. Your task is to help users by providing well-researched and accurate information based on their queries. Use the web_search tool to find reliable sources and ensure that your responses are clear and concise.""",
        },
        {"role": "user", "content": message_content},
    ]

    reply = llm_with_tools.invoke(messages)

    # Check if the model wants to use tools
    if reply.tool_calls:
        # Execute each tool call
        tool_results = []
        for tool_call in reply.tool_calls:

            tool_name = (
                tool_call["name"] if isinstance(tool_call, dict) else tool_call.name
            )
            tool_args = (
                tool_call["args"] if isinstance(tool_call, dict) else tool_call.args
            )

            if tool_name == "web_search":
                result = web_search.invoke(tool_args)
                tool_results.append(result)

        # Combine tool results into research notes
        research_notes = "\n\n".join(tool_results)

        # Optionally, get a summary from the LLM
        summary_messages = [
            {
                "role": "system",
                "content": "Summarize the following research findings into clear, organized notes.",
            },
            {"role": "user", "content": research_notes},
        ]
        summary = llm.invoke(summary_messages)
        research_notes = summary.content
    else:
        # No tool calls, use the direct response
        research_notes = reply.content

    supabase.table("agent-logs").insert(
        {
            "run_id": run_id,
            "agent": "researcher",
            "input": message_content,
            "output": research_notes,
        }
    ).execute()

    return {
        "research_notes": research_notes,
        "messages": [
            {
                "role": "assistant",
                "content": f"Research completed: {research_notes[:200]}...",
            }
        ],
    }
