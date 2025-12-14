from langgraph.graph import StateGraph, START, END
from research_agent import research_agent
from state import State
from writer_agent import writer_agent
from fack_checker_agent import fact_checker_agent
from polisher_agent import polisher_agent
from routers.fack_checker_router import fact_check_router
from langgraph.store.memory import InMemoryStore
import uuid


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

# store = InMemoryStore()

graph_builder.add_edge(START, "research_agent")

graph_builder.add_edge("research_agent", "writer_agent")
graph_builder.add_edge("writer_agent", "fact_checker_agent")
graph_builder.add_conditional_edges("fact_checker_agent", fact_check_router)
graph_builder.add_edge("polisher_agent", END)


orchestrater = graph_builder.compile()
# run_id = str(uuid.uuid4())

# state = orchestrater.invoke(
#     {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": "What are the latest advancements in renewable energy?",
#             }
#         ],
#         "run_id": run_id,
#         "retry_count": 0,
#     }
# )


# print(state.get("final_post", "No final post generated"))
