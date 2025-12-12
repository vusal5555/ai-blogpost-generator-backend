from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from state import State


load_dotenv()


llm = init_chat_model("claude-sonnet-4-5-20250929")


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
