from typing import Literal
from agents.state import State


def fact_check_router(state: State) -> Literal["polisher_agent", "writer_agent"]:
    print("Fact Check Router Invoked")

    if state.get("fact_check_passed"):
        return "polisher_agent"

    # Let the LLM decide if retry is worthwhile
    if state.get("should_retry", False):
        return "writer_agent"

    return "polisher_agent"
