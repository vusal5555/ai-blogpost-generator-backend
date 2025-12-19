from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from agents.state import State
from subapase_client import supabase
import uuid
import json


load_dotenv()


llm = init_chat_model("claude-sonnet-4-5-20250929")

MAX_RETRIES = 5  # Safety limit to prevent infinite loops


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

    print(f"Fact Checker Agent Invoked (attempt {retry_count + 1})")

    messages = [
        {
            "role": "system",
            "content": f"""You are a fact-checking agent. Your task is to verify the accuracy of the information presented in the draft based on the provided research notes.

        This is attempt {retry_count + 1} of fact-checking this draft.

        You MUST respond in the following JSON format only:
        {{
            "passed": true or false,
            "issues": "Description of issues found, or empty string if none",
            "should_retry": true or false,
            "reasoning": "Explain why retry is or isn't needed"
        }}

        Guidelines for "should_retry":
        - Set to TRUE if issues are fixable (minor inaccuracies, missing citations, unclear statements)
        - Set to FALSE if the draft is fundamentally flawed and unlikely to improve
        - Set to FALSE if issues are very minor and acceptable for publication
        - Set to FALSE if this is already attempt 3+ and issues persist (diminishing returns)

        If all facts are accurate, set "passed" to true, "issues" to "", and "should_retry" to false.""",
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

    try:
        response_text = reply.content.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        result = json.loads(response_text)
        passed = result.get("passed", False)
        issues = result.get("issues", "")
        should_retry = result.get("should_retry", False)
    except (json.JSONDecodeError, KeyError):
        passed = False
        issues = reply.content.strip()
        should_retry = retry_count < 2  # Fallback: retry twice if parsing fails

    # Safety limit
    if retry_count >= MAX_RETRIES:
        should_retry = False

    supabase.table("agent-logs").insert(
        {
            "run_id": run_id,
            "agent": "fact_checker_agent",
            "input": message_content,
            "output": reply.content,
        }
    ).execute()

    return {
        "fact_check_passed": passed,
        "fact_check_issues": issues if not passed else "",
        "retry_count": retry_count + 1,
        "should_retry": should_retry,
        "messages": [
            {"role": "assistant", "content": "Fact check passed." if passed else issues}
        ],
    }
