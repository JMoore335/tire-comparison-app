from langgraph.graph import StateGraph, END
from typing import TypedDict
import pandas as pd
from agent.tools import analyze_tires_from_df


# TireState defines the data structure that flows through the LangGraph workflow.
# Every node in the graph receives this state as input and returns an updated version of it.
class TireState(TypedDict):
    tire_size: str           # The tire size or model name used to label the analysis
    dataframe: pd.DataFrame  # The tire test data to be analyzed
    analysis: str            # The LLM-generated analysis text (populated by the node)
    error: str               # Any error message if the node fails (empty string if successful)


# This is the single node in the graph. It receives the current state,
# runs the LLM analysis on the dataframe, and returns the updated state.
# If anything goes wrong, it catches the exception and stores the error
# message in state rather than crashing the app.
def fetch_and_analyse(state: TireState) -> TireState:
    try:
        analysis = analyze_tires_from_df(state["tire_size"], state["dataframe"])
        return {**state, "analysis": analysis, "error": ""}
    except Exception as e:
        return {**state, "analysis": "", "error": str(e)}


# Assembles the LangGraph workflow. Currently a single-node graph —
# the entry point goes straight to fetch_and_analyse, which then ends.
# This structure makes it straightforward to add additional nodes later
# (e.g. a price lookup step or a data validation step) without restructuring.
def build_graph():
    graph = StateGraph(TireState)
    graph.add_node("fetch_and_analyse", fetch_and_analyse)
    graph.set_entry_point("fetch_and_analyse")
    graph.add_edge("fetch_and_analyse", END)
    return graph.compile()


# Compiled graph instance — imported and called directly by app.py
tire_graph = build_graph()