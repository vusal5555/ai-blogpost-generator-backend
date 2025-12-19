from langgraph.graph import StateGraph, START, END
from agents.research_agent import research_agent
from agents.state import State
from agents.writer_agent import writer_agent
from agents.fack_checker_agent import fact_checker_agent
from agents.polisher_agent import polisher_agent
from routers.fack_checker_router import fact_check_router


graph_builder = StateGraph(State)


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
