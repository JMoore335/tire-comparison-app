import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from agent.graph import tire_graph
from data.cache import get_all_sizes, init_db

# Initialise database on startup
init_db()

# Page config
st.set_page_config(
    page_title="Tyre Performance Comparison",
    page_icon="🏎️",
    layout="wide"
)

st.title("🏎️ Tyre Performance Comparison")
st.markdown("Compare **Michelin, Goodyear, Continental and Bridgestone** using real professional test data from TyreReviews.")

# Sidebar
st.sidebar.header("Search")
available_sizes = get_all_sizes()

if available_sizes:
    st.sidebar.markdown(f"**{len(available_sizes)} tyre sizes** in database.")
else:
    st.sidebar.warning("No data in database yet. Run `python scripts/fetch_data.py` first.")

tire_size = st.sidebar.text_input(
    "Enter tyre size",
    placeholder="e.g. 225/45 R17",
    help="Enter the tyre size in standard format, e.g. 225/45 R17"
)

if available_sizes:
    st.sidebar.markdown("**Available sizes:**")
    for size in available_sizes:
        st.sidebar.markdown(f"- {size}")

search = st.sidebar.button("Compare Tyres", type="primary")

# Main content
if search and tire_size:
    with st.spinner("Fetching data and running analysis..."):
        result = tire_graph.invoke({
            "tire_size": tire_size,
            "dataframe": pd.DataFrame(),
            "analysis": "",
            "error": ""
        })

    if result["error"]:
        st.error(f"Something went wrong: {result['error']}")

    elif result["dataframe"].empty:
        st.warning(f"No results found for size **{tire_size}**. Check the available sizes in the sidebar.")

    else:
        df = result["dataframe"]
        analysis = result["analysis"]

        st.success(f"Found **{len(df)} results** for size **{tire_size}**")

        # --- Metrics Table ---
        st.subheader("📊 Test Results")

        display_cols = {
            "brand": "Brand",
            "model": "Model",
            "test_year": "Year",
            "test_vehicle": "Test Vehicle",
            "wet_braking": "Wet Braking (m)",
            "dry_braking": "Dry Braking (m)",
            "wet_handling": "Wet Handling (s)",
            "dry_handling": "Dry Handling (s)",
            "straight_aquaplaning": "Aquaplaning (km/h)",
            "noise_db": "Noise (dB)",
            "subj_comfort": "Comfort",
            "test_name": "Test"
        }

        available_cols = {k: v for k, v in display_cols.items() if k in df.columns}
        display_df = df[list(available_cols.keys())].rename(columns=available_cols)
        st.dataframe(display_df, use_container_width=True)

        # --- Radar Chart ---
        numeric_metrics = {
            "Wet Braking (m)": "wet_braking",
            "Dry Braking (m)": "dry_braking",
            "Wet Handling (s)": "wet_handling",
            "Dry Handling (s)": "dry_handling",
            "Noise (dB)": "noise_db",
        }

        # Only include metrics that exist and have data
        valid_metrics = {
            label: col for label, col in numeric_metrics.items()
            if col in df.columns and df[col].notna().any()
        }

        if len(valid_metrics) >= 3:
            st.subheader("🕸️ Performance Radar Chart")
            st.caption("Note: For braking and handling, lower values are better. Chart inverts these so larger = better for all metrics.")

            fig = go.Figure()
            brands_in_data = df["brand"].unique()

            for brand in brands_in_data:
                brand_df = df[df["brand"] == brand]
                values = []
                for label, col in valid_metrics.items():
                    val = brand_df[col].mean()
                    values.append(val)

                # Invert braking/handling so lower = better displays correctly
                inverted = []
                for i, (label, col) in enumerate(valid_metrics.items()):
                    if any(x in label.lower() for x in ["braking", "handling", "noise"]):
                        # Invert: use max - value so smaller original = larger on chart
                        all_vals = df[col].dropna()
                        if not all_vals.empty:
                            inverted.append(all_vals.max() + all_vals.min() - values[i])
                        else:
                            inverted.append(values[i])
                    else:
                        inverted.append(values[i])

                labels = list(valid_metrics.keys())
                fig.add_trace(go.Scatterpolar(
                    r=inverted,
                    theta=labels,
                    fill="toself",
                    name=brand
                ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=False)),
                showlegend=True,
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

        # --- LLM Analysis ---
        st.subheader("🤖 AI Analysis")
        st.markdown(analysis)

elif search and not tire_size:
    st.warning("Please enter a tyre size before searching.")

else:
    st.info("👈 Enter a tyre size in the sidebar and click **Compare Tyres** to get started.")
    st.markdown("""
    ### How it works
    1. Enter a tyre size (e.g. `225/45 R17`)
    2. The app queries real professional test data from TyreReviews
    3. Results are displayed in a table and radar chart
    4. An AI analyst summarises the key findings

    ### Data source
    All data comes from **TyreReviews professional tests** — instrumented, controlled measurements
    including wet and dry braking distances, handling lap times, and aquaplaning speeds.
    """)