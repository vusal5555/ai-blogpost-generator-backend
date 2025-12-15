from typing import Literal
from agents.state import State


def fact_check_router(state: State) -> Literal["polisher_agent", "writer_agent"]:
    print("Fact Check Router Invoked")
    if state.get("fact_check_passed"):
        return "polisher_agent"
    if state.get("retry_count", 0) >= 2:
        return "polisher_agent"
    return "writer_agent"
