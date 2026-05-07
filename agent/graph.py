from langgraph.graph import StateGraph, END
from typing import TypedDict
import pandas as pd
from agent.tools import analyse_tires

class TireState(TypedDict):
    tire_size: str
    dataframe: pd.DataFrame
    analysis: str
    error: str

def fetch_and_analyse(state: TireState) -> TireState:
    """Single node that fetches data and runs LLM analysis."""
    try:
        df, analysis = analyse_tires(state["tire_size"])
        return {
            **state,
            "dataframe": df,
            "analysis": analysis,
            "error": ""
        }
    except Exception as e:
        return {
            **state,
            "dataframe": pd.DataFrame(),
            "analysis": "",
            "error": str(e)
        }

def build_graph():
    """Build and compile the LangGraph workflow."""
    graph = StateGraph(TireState)
    graph.add_node("fetch_and_analyse", fetch_and_analyse)
    graph.set_entry_point("fetch_and_analyse")
    graph.add_edge("fetch_and_analyse", END)
    return graph.compile()

# Compiled graph — imported by app.py
tire_graph = build_graph()