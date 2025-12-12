from typing import Literal
from langgraph.graph import StateGraph, START, END
from research_agent import research_agent
from state import State
from writer_agent import writer_agent
from fack_checker_agent import fact_checker_agent
from polisher_agent import polisher_agent


graph_builder = StateGraph(State)


def fact_check_router(state: State) -> Literal["polisher_agent", "writer_agent"]:
    print("Fact Check Router Invoked")
    if state.get("fact_check_passed"):
        return "polisher_agent"
    if state.get("retry_count", 0) >= 2:
        return "polisher_agent"
    return "writer_agent"


graph_builder.add_node(
    "research_agent",
    research_agent,
)
graph_builder.add_node(
    "writer_agent",
    writer_agent,
)


graph_builder.add_node(
    "fact_checker_agent",
    fact_checker_agent,
)

graph_builder.add_node(
    "polisher_agent",
    polisher_agent,
)


graph_builder.add_edge(START, "research_agent")

graph_builder.add_edge("research_agent", "writer_agent")
graph_builder.add_edge("writer_agent", "fact_checker_agent")
graph_builder.add_conditional_edges("fact_checker_agent", fact_check_router)
graph_builder.add_edge("polisher_agent", END)


orchestrater = graph_builder.compile()


state = orchestrater.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "What are the latest advancements in renewable energy?",
            }
        ],
        "retry_count": 0,
    }
)

print(state.get("final_post", "No final post generated"))
