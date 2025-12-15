from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from agents.state import State
from subapase_client import supabase
import uuid


load_dotenv()


llm = init_chat_model("claude-sonnet-4-5-20250929")


def fact_checker_agent(state: State):
    draft = state.get("draft", "")
    research_notes = state.get("research_notes", "")
    retry_count = state.get("retry_count", 0)
    last_message = state["messages"][-1]
    message_content = (
        last_message.content
        if hasattr(last_message, "content")
        else last_message["content"]
    )
    run_id = state.get("run_id") or str(uuid.uuid4())

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
        supabase.table("agent-logs").insert(
            {
                "run_id": run_id,
                "agent": "fact_checker_agent",
                "input": message_content,
                "output": reply.content,
            }
        ).execute()

        return {
            "fact_check_passed": False,
            "fact_check_issues": issues,
            "retry_count": retry_count + 1,
            "messages": [{"role": "assistant", "content": issues}],
        }
