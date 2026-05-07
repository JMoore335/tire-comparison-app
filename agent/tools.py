import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from agent.prompts import ANALYSIS_PROMPT
from data.cache import query_by_size
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))

def get_tire_dataframe(tire_size: str) -> pd.DataFrame:
    """Query the database and return results as a DataFrame."""
    rows = query_by_size(tire_size)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)

def format_tire_data_for_llm(df: pd.DataFrame) -> str:
    """Format the DataFrame into readable text for the LLM."""
    if df.empty:
        return "No data available."

    lines = []
    for _, row in df.iterrows():
        line = f"Brand: {row['brand']} | Model: {row['model']} | Test: {row['test_name']}"
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

def analyse_tires(tire_size: str) -> tuple[pd.DataFrame, str]:
    """
    Main function called by the app.
    Returns the DataFrame for display and the LLM analysis as a string.
    """
    df = get_tire_dataframe(tire_size)

    if df.empty:
        return df, f"No data found for size {tire_size}. Try running the scraper first."

    formatted = format_tire_data_for_llm(df)
    prompt = ANALYSIS_PROMPT.format(tire_size=tire_size, tire_data=formatted)

    response = llm.invoke([HumanMessage(content=prompt)])
    analysis = response.content

    return df, analysis