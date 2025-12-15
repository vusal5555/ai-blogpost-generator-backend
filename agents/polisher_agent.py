from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from agents.state import State
from subapase_client import supabase
import uuid


load_dotenv()


llm = init_chat_model("claude-sonnet-4-5-20250929")


def polisher_agent(state: State):
    print("Polisher Agent Invoked")
    run_id = state.get("run_id") or str(uuid.uuid4())
    draft = state.get("draft", "")
    last_message = state["messages"][-1]
    message_content = (
        last_message.content
        if hasattr(last_message, "content")
        else last_message["content"]
    )
    messages = [
        {
            "role": "system",
            "content": """You are a content polishing agent. Your task is to refine and enhance the draft to ensure it is polished, coherent, and engaging. Focus on improving grammar, style, and overall readability while maintaining the original message and intent of the content. Ensure that the final output is professional and ready for publication. make sure that all the extra charachers are removed such and make sure that titles and subtitles are properly formatted, they are bold and they don't containe these characters - ###.""",
        },
        {"role": "user", "content": draft},
    ]

    reply = llm.invoke(messages)

    supabase.table("agent-logs").insert(
        {
            "run_id": run_id,
            "agent": "polisher_agent",
            "input": message_content,
            "output": reply.content,
        }
    ).execute()
    return {
        "final_post": reply.content,
        "messages": [{"role": "assistant", "content": reply.content}],
    }
