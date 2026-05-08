import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from agent.graph import tire_graph
from data.cache import (
    get_all_sizes, get_all_models, query_by_size,
    query_by_model, get_metric_ranges, init_db
)

init_db()

st.set_page_config(
    page_title="Tire Performance Comparison",
    page_icon="",
    layout="wide"
)

st.title("Tire Performance Comparison")
st.markdown("Compare tires using real professional test data from **TyreReviews**.")

# Session state
if "selected_size" not in st.session_state:
    st.session_state.selected_size = ""
if "selected_model" not in st.session_state:
    st.session_state.selected_model = ""
if "search_mode" not in st.session_state:
    st.session_state.search_mode = "size"

@st.cache_data
def load_metric_ranges():
    return get_metric_ranges()

@st.cache_data
def load_all_models():
    return get_all_models()

metric_ranges = load_metric_ranges()
all_models = load_all_models()

available_sizes = get_all_sizes()

# Sidebar - Model search first
st.sidebar.header("Search by Tire Model")

model_options = [""] + [f"{brand} - {model}" for brand, model in all_models]
selected_model_label = st.sidebar.selectbox(
    "Select a tire model",
    options=model_options,
    index=0,
    key="model_selectbox"
)

if selected_model_label:
    selected_model_name = selected_model_label.split(" - ", 1)[1]
    if selected_model_name != st.session_state.selected_model:
        st.session_state.selected_model = selected_model_name
        st.session_state.search_mode = "model"
        st.rerun()

st.sidebar.markdown("---")

# Sidebar - Size search second
st.sidebar.header("Search by Tire Size")

if available_sizes:
    st.sidebar.markdown(f"**{len(available_sizes)} tire sizes** in database.")
else:
    st.sidebar.warning("No data found. Run `python scripts/fetch_data.py` first.")

tire_size_input = st.sidebar.text_input(
    "Enter tire size",
    value=st.session_state.selected_size,
    placeholder="e.g. 225/45 R17",
    help="Enter the tire size in standard format"
)

if tire_size_input != st.session_state.selected_size:
    st.session_state.selected_size = tire_size_input
    st.session_state.search_mode = "size"

if available_sizes:
    st.sidebar.markdown("**Available sizes:**")
    for size in available_sizes:
        if st.sidebar.button(size, key=f"size_btn_{size}"):
            st.session_state.selected_size = size
            st.session_state.search_mode = "size"
            st.rerun()

# Constants
DISPLAY_COLS = {
    "model":                "Model",
    "computed_rank":        "Rank",
    "overall_score_pct":    "Relative Score (%)",
    "dry_braking":          "Dry Braking (m)",
    "dry_handling":         "Dry Handling (s)",
    "wet_braking":          "Wet Braking (m)",
    "wet_handling":         "Wet Handling (s)",
    "straight_aquaplaning": "Aquaplaning (km/h)",
}

NUMERIC_METRICS = {
    "Dry Braking (m)":    "dry_braking",
    "Dry Handling (s)":   "dry_handling",
    "Wet Braking (m)":    "wet_braking",
    "Wet Handling (s)":   "wet_handling",
    "Aquaplaning (km/h)": "straight_aquaplaning",
}

METRIC_UNITS = {
    "Dry Braking (m)":    "Distance (m)",
    "Dry Handling (s)":   "Lap Time (s)",
    "Wet Braking (m)":    "Distance (m)",
    "Wet Handling (s)":   "Lap Time (s)",
    "Aquaplaning (km/h)": "Speed (km/h)",
}

LOWER_IS_BETTER = {"wet_braking", "dry_braking", "wet_handling", "dry_handling"}

RANK_METRICS = {
    "dry_braking":          "lower",
    "dry_handling":         "lower",
    "wet_braking":          "lower",
    "wet_handling":         "lower",
    "straight_aquaplaning": "higher",
}

COLUMN_COLORING = {
    "Relative Score (%)":  "RdYlGn",
    "Dry Braking (m)":     "RdYlGn_r",
    "Dry Handling (s)":    "RdYlGn_r",
    "Wet Braking (m)":     "RdYlGn_r",
    "Wet Handling (s)":    "RdYlGn_r",
    "Aquaplaning (km/h)":  "RdYlGn",
}

METRIC_BOUNDS = {
    "wet_braking":          (15, 80),
    "dry_braking":          (15, 60),
    "wet_handling":         (60, 200),
    "dry_handling":         (60, 200),
    "straight_aquaplaning": (40, 120),
    "curved_aquaplaning":   (0, 20),
    "overall_score":        (0, 100),
}

METRIC_DESCRIPTIONS = {
    "Dry Braking (m)":    ("Distance to stop from 100 km/h on a dry surface.", "Lower is better"),
    "Dry Handling (s)":   ("Lap time on a dry handling circuit.", "Lower is better"),
    "Wet Braking (m)":    ("Distance to stop from 80 km/h on a wet surface.", "Lower is better"),
    "Wet Handling (s)":   ("Lap time on a wet handling circuit.", "Lower is better"),
    "Aquaplaning (km/h)": ("Speed at which the tire begins to lose contact with a wet surface.", "Higher is better"),
}


def clean_outliers(df):
    df = df.copy()
    for col, (lo, hi) in METRIC_BOUNDS.items():
        if col in df.columns:
            df.loc[~df[col].between(lo, hi), col] = np.nan
    return df


def get_valid_metrics(df):
    return {
        label: col for label, col in NUMERIC_METRICS.items()
        if col in df.columns and df[col].notna().any()
    }


def compute_test_rank(df):
    df = df.copy()

    test_available = [
        col for col in RANK_METRICS
        if col in df.columns and df[col].notna().any()
    ]

    if not test_available:
        df["overall_score_pct"] = None
        df["computed_rank"] = None
        df["data_completeness"] = None
        return df

    score_list = []
    completeness_list = []

    for idx, row in df.iterrows():
        tire_scores = []
        tire_count = 0

        for col in test_available:
            val = row.get(col)
            if pd.isna(val):
                continue

            tire_count += 1
            direction = RANK_METRICS[col]

            if direction == "lower":
                best = df[col].dropna().min()
                if best == 0:
                    continue
                score = (best / val) * 100
            else:
                best = df[col].dropna().max()
                if best == 0:
                    continue
                score = (val / best) * 100

            tire_scores.append(score)

        overall = round(np.mean(tire_scores), 2) if tire_scores else None
        completeness = round((tire_count / len(test_available)) * 100) if test_available else None

        score_list.append(overall)
        completeness_list.append(completeness)

    df["overall_score_pct"] = score_list
    df["data_completeness"] = completeness_list
    df["computed_rank"] = df["overall_score_pct"].rank(
        ascending=False, method="min", na_option="bottom"
    ).astype("Int64")

    return df


def show_metric_descriptions():
    with st.expander("About the performance metrics"):
        rows = []
        for metric, (desc, direction) in METRIC_DESCRIPTIONS.items():
            rows.append({
                "Metric": metric,
                "Description": desc,
                "Direction": direction
            })
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )


def show_table_heatmap(df, highlight_model=None):
    cols_to_show = {k: v for k, v in DISPLAY_COLS.items() if k in df.columns}
    display_df = df[list(cols_to_show.keys())].rename(columns=cols_to_show).reset_index(drop=True)

    if "Rank" in display_df.columns:
        display_df = display_df.sort_values("Rank", ascending=True).reset_index(drop=True)

    if "Rank" in display_df.columns:
        display_df["Rank"] = pd.to_numeric(display_df["Rank"], errors="coerce")
        display_df["Rank"] = display_df["Rank"].apply(
            lambda x: int(x) if pd.notna(x) else ""
        )

    format_dict = {
        col: "{:.2f}" for col in display_df.columns
        if display_df[col].dtype in ["float64", "float32"]
    }

    colorable_cols = {k: v for k, v in DISPLAY_COLS.items()
                      if v in display_df.columns and v in COLUMN_COLORING}

    styled = display_df.style

    for db_col, display_col in colorable_cols.items():
        cmap = COLUMN_COLORING.get(display_col)
        if cmap and display_df[display_col].notna().any():
            styled = styled.background_gradient(
                subset=[display_col],
                cmap=cmap,
                axis=0
            )

    if format_dict:
        styled = styled.format(format_dict, na_rep="")

    if highlight_model and "Model" in display_df.columns:
        def highlight_row(row):
            if row.get("Model") == highlight_model:
                return ["font-weight: bold; color: #0066cc"] * len(row)
            return [""] * len(row)
        styled = styled.apply(highlight_row, axis=1)

    st.dataframe(styled, use_container_width=True, hide_index=True)


def show_bar_charts(df, highlight_model=None):
    valid_metrics = get_valid_metrics(df)
    if not valid_metrics:
        st.info("No metrics available.")
        return

    for label, col in valid_metrics.items():
        plot_df = df[["model", col]].dropna(subset=[col]).copy()
        if plot_df.empty:
            continue

        lower_better = col in LOWER_IS_BETTER
        plot_df = plot_df.sort_values(col, ascending=not lower_better)
        plot_df[col] = plot_df[col].round(2)

        if highlight_model:
            colors = [
                "#2ecc71" if m == highlight_model else "#5b9bd5"
                for m in plot_df["model"]
            ]
        else:
            colors = ["#5b9bd5"] * len(plot_df)

        data_min = plot_df[col].min()
        data_max = plot_df[col].max()
        padding = (data_max - data_min) * 0.3
        x_range = [
            round(data_min - padding, 2),
            round(data_max + padding, 2)
        ]

        y_label = METRIC_UNITS.get(label, "Value")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=plot_df[col],
            y=plot_df["model"],
            orientation="h",
            marker_color=colors,
            text=[f"{v:.2f}" for v in plot_df[col]],
            textposition="outside",
            cliponaxis=False
        ))

        fig.update_layout(
            title=f"{label} ({'lower is better' if lower_better else 'higher is better'})",
            height=max(300, len(plot_df) * 45),
            margin=dict(t=50, b=40, l=20, r=80),
            xaxis=dict(
                title=y_label,
                range=x_range
            ),
            yaxis=dict(),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)


def compute_relative_performance(df_all):
    df_clean = clean_outliers(df_all)
    records = []

    for test_url, test_df in df_clean.groupby("test_url"):
        for _, row in test_df.iterrows():
            for label, col in NUMERIC_METRICS.items():
                if col not in test_df.columns:
                    continue
                tire_val = row.get(col)
                if pd.isna(tire_val):
                    continue

                test_vals = test_df[col].dropna()
                if len(test_vals) < 2:
                    continue

                test_avg = test_vals.mean()
                if test_avg == 0:
                    continue

                if col in LOWER_IS_BETTER:
                    relative = (test_avg - tire_val) / test_avg * 100
                else:
                    relative = (tire_val - test_avg) / test_avg * 100

                records.append({
                    "brand": row["brand"],
                    "model": row["model"],
                    "metric": label,
                    "relative": relative,
                    "test_count": 1
                })

    if not records:
        return pd.DataFrame()

    records_df = pd.DataFrame(records)

    agg = records_df.groupby(["brand", "model", "metric"]).agg(
        avg_relative=("relative", "mean"),
        appearances=("test_count", "sum")
    ).reset_index()

    pivot = agg.pivot_table(
        index=["brand", "model"],
        columns="metric",
        values="avg_relative"
    ).reset_index()

    appearances = records_df.groupby(["brand", "model"])["test_count"].sum().reset_index()
    appearances.columns = ["brand", "model", "tests"]
    pivot = pivot.merge(appearances, on=["brand", "model"])

    metric_cols = [c for c in pivot.columns if c in NUMERIC_METRICS]
    pivot["Relative Score (%)"] = pivot[metric_cols].mean(axis=1).round(2)
    pivot = pivot.sort_values("Relative Score (%)", ascending=False)
    pivot["Rank"] = pivot["Relative Score (%)"].rank(
        ascending=False, method="min"
    ).astype(int)

    return pivot


def show_cross_test_comparison(df_all, highlight_model=None):
    st.subheader("Cross-Test Relative Performance")
    st.markdown(
        "Each tire's performance expressed as **% better or worse than the average "
        "competitor in each test it appeared in**. Positive = better than average. "
        "Scores are averaged across all tests the tire appeared in, normalising for "
        "vehicle and conditions. Outliers are excluded using physical bounds."
    )

    pivot = compute_relative_performance(df_all)

    if pivot.empty:
        st.info("Not enough data to compute relative performance.")
        return

    ordered_metrics = [m for m in NUMERIC_METRICS if m in pivot.columns]
    display_cols = ["model", "Rank", "Relative Score (%)"] + ordered_metrics
    display_cols = [c for c in display_cols if c in pivot.columns]

    display_df = pivot[display_cols].reset_index(drop=True)

    format_cols = [c for c in ordered_metrics + ["Relative Score (%)"]
                   if c in display_df.columns]
    gradient_cols = format_cols

    def highlight_model_row(row):
        if highlight_model and row.get("model") == highlight_model:
            return ["font-weight: bold; color: #0066cc"] * len(row)
        return [""] * len(row)

    styled = (
        display_df.style
        .background_gradient(subset=gradient_cols, cmap="RdYlGn", axis=0)
        .format({col: "{:.2f}" for col in format_cols})
        .apply(highlight_model_row, axis=1)
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)
    st.caption(
        "% above/below test average. Green = consistently above average. "
        "Red = consistently below average."
    )


def show_per_test_sections(grouped, highlight_model=None):
    for test_url, group_df in grouped:
        test_name = group_df["test_name"].iloc[0]
        test_vehicle = group_df["test_vehicle"].iloc[0]
        test_year = group_df["test_year"].iloc[0]
        tire_size = group_df["tire_size"].iloc[0]

        st.markdown("---")
        st.subheader(f"{test_vehicle} - {test_year} - {tire_size}")
        st.caption(f'"{test_name}"')

        ranked_df = compute_test_rank(group_df)

        st.markdown("**Test Results**")
        show_table_heatmap(ranked_df, highlight_model=highlight_model)

        if "data_completeness" in ranked_df.columns:
            incomplete = ranked_df[ranked_df["data_completeness"] < 100]
            if not incomplete.empty:
                missing_models = ", ".join(incomplete["model"].tolist())
                n_available = len([
                    col for col in RANK_METRICS
                    if col in ranked_df.columns and ranked_df[col].notna().any()
                ])
                st.warning(
                    f"Some tires have incomplete metric data: **{missing_models}**. "
                    f"Their scores are calculated from available metrics only "
                    f"(out of {n_available} metrics tested). "
                    f"This may affect rank comparability."
                )

        st.markdown("**Bar Charts**")
        show_bar_charts(ranked_df, highlight_model=highlight_model)


def run_llm_analysis(label, df_all):
    st.markdown("---")
    st.subheader("AI Analysis")
    st.caption(
        "The AI analysis covers all tests shown above. "
        "For direct comparisons, refer to results within the same test group."
    )

    with st.spinner("Running AI analysis..."):
        result = tire_graph.invoke({
            "tire_size": label,
            "test_url": "",
            "dataframe": df_all,
            "analysis": "",
            "error": ""
        })

    if result["error"]:
        st.error(f"Something went wrong: {result['error']}")
    else:
        st.markdown(result["analysis"])


# ---- Main content ----

if st.session_state.search_mode == "size" and st.session_state.selected_size:
    tire_size = st.session_state.selected_size
    rows = query_by_size(tire_size)

    if not rows:
        st.warning(f"No results found for **{tire_size}**. Check the available sizes in the sidebar.")
    else:
        df_all = clean_outliers(pd.DataFrame(rows))
        st.success(
            f"Found **{len(df_all)} results** for **{tire_size}** across "
            f"**{df_all['test_url'].nunique()}** tests."
        )

        show_metric_descriptions()

        grouped = df_all.groupby("test_url")

        st.subheader("Tests Found")
        summary_rows = []
        for test_url, group_df in grouped:
            summary_rows.append({
                "Test": f'"{group_df["test_name"].iloc[0]}"',
                "Year": group_df["test_year"].iloc[0],
                "Vehicle": group_df["test_vehicle"].iloc[0],
                "Tires Tested": len(group_df),
                "Brands Included": ", ".join(sorted(group_df["brand"].unique()))
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
        st.caption("Each test group below shows only tires tested under identical conditions on the same vehicle.")

        show_cross_test_comparison(df_all)

        st.markdown("---")
        st.subheader("Individual Test Results by Vehicle")
        st.caption("Each section below shows results from a single test where all tires were tested on the same vehicle under identical conditions.")

        show_per_test_sections(grouped)
        run_llm_analysis(tire_size, df_all)

elif st.session_state.search_mode == "model" and st.session_state.selected_model:
    selected_model = st.session_state.selected_model
    rows = query_by_model(selected_model)

    if not rows:
        st.warning(f"No comparison data found for **{selected_model}**.")
    else:
        df_all = clean_outliers(pd.DataFrame(rows))
        num_tests = df_all["test_url"].nunique()
        st.success(
            f"Showing all tests where **{selected_model}** appeared - "
            f"{num_tests} test(s), same vehicle and tire size only."
        )

        show_metric_descriptions()

        grouped = df_all.groupby("test_url")

        st.subheader("Tests Found")
        summary_rows = []
        for test_url, group_df in grouped:
            summary_rows.append({
                "Test": f'"{group_df["test_name"].iloc[0]}"',
                "Year": group_df["test_year"].iloc[0],
                "Vehicle": group_df["test_vehicle"].iloc[0],
                "Tire Size": group_df["tire_size"].iloc[0],
                "Tires in Test": len(group_df),
                "Brands Included": ", ".join(sorted(group_df["brand"].unique()))
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
        st.caption(
            f"Highlighted rows show {selected_model}. "
            "Only tires tested on the same vehicle with the same tire size are included."
        )

        show_cross_test_comparison(df_all, highlight_model=selected_model)

        st.markdown("---")
        st.subheader("Individual Test Results by Vehicle")
        st.caption("Each section below shows results from a single test where all tires were tested on the same vehicle under identical conditions.")

        show_per_test_sections(grouped, highlight_model=selected_model)
        run_llm_analysis(selected_model, df_all)

else:
    show_metric_descriptions()
    st.info("Enter a tire size or select a tire model from the sidebar to get started.")
    st.markdown("""
    ### How it works

    **Search by Tire Model**
    Select a specific tire model to see how it performed across every test it appeared in,
    always compared only against tires tested on the same vehicle and in the same size.

    **Search by Tire Size**
    Enter a tire size (e.g. 225/45 R17) or click one from the sidebar. Results are grouped
    by test - each group used the same vehicle under identical conditions.

    ### Data source
    All data comes from **TyreReviews professional tests** - instrumented measurements
    including wet and dry braking distances, handling lap times, and aquaplaning speeds.
    """)