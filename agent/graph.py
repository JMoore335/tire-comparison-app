from langgraph.graph import StateGraph, END
from typing import TypedDict
import pandas as pd
from agent.tools import analyse_tires_from_df

class TireState(TypedDict):
    tire_size: str
    test_url: str
    dataframe: pd.DataFrame
    analysis: str
    error: str

def fetch_and_analyse(state: TireState) -> TireState:
    try:
        analysis = analyse_tires_from_df(state["tire_size"], state["dataframe"])
        return {
            **state,
            "analysis": analysis,
            "error": ""
        }
    except Exception as e:
        return {
            **state,
            "analysis": "",
            "error": str(e)
        }

def build_graph():
    graph = StateGraph(TireState)
    graph.add_node("fetch_and_analyse", fetch_and_analyse)
    graph.set_entry_point("fetch_and_analyse")
    graph.add_edge("fetch_and_analyse", END)
    return graph.compile()

tire_graph = build_graph()