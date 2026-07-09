from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.state import InterviewState
from app.graph.nodes import start_interview_node, process_turn_node, route_entry

def build_interview_graph():
    graph = StateGraph(InterviewState)

    graph.add_node("start_interview", start_interview_node)
    graph.add_node("process_turn", process_turn_node)

    graph.set_conditional_entry_point(
        route_entry,
        {"start": "start_interview", "turn": "process_turn"},
    )

    graph.add_edge("start_interview", END)
    graph.add_edge("process_turn", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# Singleton compiled graph, reused across requests.
interview_graph = build_interview_graph()
