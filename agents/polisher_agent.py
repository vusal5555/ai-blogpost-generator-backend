from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from state import State


load_dotenv()


llm = init_chat_model("claude-sonnet-4-5-20250929")


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
