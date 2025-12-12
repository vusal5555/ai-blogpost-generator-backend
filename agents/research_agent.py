from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from state import State
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tools.web_search_tool import web_search


load_dotenv()


llm = init_chat_model("claude-sonnet-4-5-20250929")

llm.bind_tools([web_search])


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
