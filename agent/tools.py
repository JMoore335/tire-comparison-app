import os
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from agent.prompts import ANALYSIS_PROMPT
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))


def format_tire_data_for_llm(df: pd.DataFrame) -> str:
    """Format the DataFrame into readable text for the LLM."""
    if df.empty:
        return "No data available."

    lines = []
    for _, row in df.iterrows():
        line = f"Brand: {row['brand']} | Model: {row['model']} | Test: {row['test_name']} | Vehicle: {row['test_vehicle']}"
        metrics = []
        if row.get("dry_braking"):
            metrics.append(f"Dry Braking: {row['dry_braking']}m")
        if row.get("dry_handling"):
            metrics.append(f"Dry Handling: {row['dry_handling']}s")
        if row.get("wet_braking"):
            metrics.append(f"Wet Braking: {row['wet_braking']}m")
        if row.get("wet_handling"):
            metrics.append(f"Wet Handling: {row['wet_handling']}s")
        if row.get("straight_aquaplaning"):
            metrics.append(f"Aquaplaning: {row['straight_aquaplaning']}km/h")
        if metrics:
            line += "\n  " + " | ".join(metrics)
        lines.append(line)

    return "\n\n".join(lines)


def analyze_tires_from_df(tire_size: str, df: pd.DataFrame) -> str:
    """Run LLM analysis on an already-fetched DataFrame."""
    if df.empty:
        return "No data available to analyze."

    formatted = format_tire_data_for_llm(df)
    prompt = ANALYSIS_PROMPT.format(tire_size=tire_size, tire_data=formatted)
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content