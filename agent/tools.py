import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from agent.prompts import ANALYSIS_PROMPT
from data.cache import query_by_size_and_test
from dotenv import load_dotenv
import pandas as pd

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
        if row.get("wet_braking"):
            metrics.append(f"Wet Braking: {row['wet_braking']}m")
        if row.get("dry_braking"):
            metrics.append(f"Dry Braking: {row['dry_braking']}m")
        if row.get("wet_handling"):
            metrics.append(f"Wet Handling: {row['wet_handling']}s")
        if row.get("dry_handling"):
            metrics.append(f"Dry Handling: {row['dry_handling']}s")
        if row.get("straight_aquaplaning"):
            metrics.append(f"Straight Aquaplaning: {row['straight_aquaplaning']}km/h")
        if row.get("curved_aquaplaning"):
            metrics.append(f"Curved Aquaplaning: {row['curved_aquaplaning']}m/s²")
        if row.get("noise_db"):
            metrics.append(f"Noise: {row['noise_db']}dB")
        if row.get("subj_comfort"):
            metrics.append(f"Comfort: {row['subj_comfort']}")
        if metrics:
            line += "\n  " + " | ".join(metrics)
        lines.append(line)

    return "\n\n".join(lines)

def analyse_tires_from_df(tire_size: str, df: pd.DataFrame) -> str:
    """Run LLM analysis on an already-fetched DataFrame."""
    if df.empty:
        return "No data available to analyse."

    formatted = format_tire_data_for_llm(df)
    prompt = ANALYSIS_PROMPT.format(tire_size=tire_size, tire_data=formatted)
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content

def analyse_tires(tire_size: str, test_url: str) -> tuple[pd.DataFrame, str]:
    """Fetch data by test URL and run LLM analysis."""
    from data.cache import query_by_size_and_test
    rows = query_by_size_and_test(tire_size, test_url)
    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    analysis = analyse_tires_from_df(tire_size, df)
    return df, analysis