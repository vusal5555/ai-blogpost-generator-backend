from typing import Annotated
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Optional


class State(TypedDict):
    messages: Annotated[list, add_messages]
    research_notes: Optional[str]
    draft: Optional[str]
    fact_check_passed: Optional[bool]
    fact_check_issues: Optional[str]
    final_post: Optional[str]
    retry_count: int
