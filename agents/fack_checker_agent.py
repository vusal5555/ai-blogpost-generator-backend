from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from state import State


load_dotenv()


llm = init_chat_model("claude-sonnet-4-5-20250929")


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
