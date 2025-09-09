import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
import os
import pandas as pd


def selectors():
    # Define min and max dates with a slider

    start_year, end_year = st.slider("Select year range", 2000, 2025, (2010, 2020))

    col1, col2 = st.columns(2)
    with col1:
        selected_stocks = st.multiselect(
            "Select stock indices",
            # TODO - update w column names
            # options=["FTSE100", "S&P 500", "DAX", "Nikkei 225", "Hang Seng"],
            options=st.session_state.combined_stocks.columns.to_list(),
            default=["FTSE100_1985to2025"],
        )

    with col2:
        selected_transport_modes = st.multiselect(
            "Select transportation modes",
            # TODO - update w column names
            # options=["Tube", "Bus and Coach", "Train"],  # TODO
            options=st.session_state.combined_fares.columns.to_list(),
            default=["singleZ1toZ4Cash"],
        )

    return start_year, end_year, selected_transport_modes, selected_stocks


def dashboard() -> None:
    st.write("Welcome.")
    st.write(
        "This interactive dashboard compares transportation costs in the UK with global stock indices."
    )
    st.write("Dataset:")
    # st.write(st.session_state.combined_fares.columns.to_list())
    # st.write(st.session_state.combined_stocks.columns.to_list())

    start_year, end_year, selected_transport_modes, selected_stocks = selectors()

    # Render the plot if there is at least one selection in each category
    if selected_stocks and selected_transport_modes:
        st.write(
            f"Selections ---- Start year: {start_year}, end year: {end_year}, stocks: {selected_stocks}, transport modes: {selected_transport_modes}"
        )
        fig = comparison_plot(
            selected_fares=selected_transport_modes,
            selected_stocks=selected_stocks,
            start_year=start_year,
            end_year=end_year,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(
            "Please select at least one stock index and one transportation mode to display the graph."
        )


############## DATA ##############
DATA_DIR = Path(__file__).parents[2] / "data"
FARE_PRICES_DIR = DATA_DIR / "fares"
STOCK_PRICES_DIR = DATA_DIR / "stocks"


def init_session_state() -> None:
    if "combined_fares" not in st.session_state:
        st.session_state.combined_fares = pd.read_csv(
            FARE_PRICES_DIR / "processed" / "combined_transport_fares.csv"
        )

    if "combined_stocks" not in st.session_state:
        st.session_state.combined_stocks = pd.read_csv(
            STOCK_PRICES_DIR / "combined_indices.csv"
        )


############## UTILS ##############
# TODO - move members to utils.py
LINE_AND_MARKER = "lines+markers"


def comparison_plot(selected_fares, selected_stocks, start_year, end_year):
    combined_stocks, combined_fares = (
        st.session_state.combined_stocks,
        st.session_state.combined_fares,
    )
    filtered_stocks = combined_stocks.loc[
        (combined_stocks.year >= start_year) & (combined_stocks.year <= end_year)
    ]
    filtered_fares = combined_fares.loc[
        (combined_fares.year >= start_year) & (combined_fares.year <= end_year)
    ]
    normalised_stocks = normalise_df_to_first_value_per_col(filtered_stocks)
    normalised_fares = normalise_fares_to_stock_anchor(
        filtered_fares, normalised_stocks
    )

    fig = go.Figure()
    # Add stock indices as dashed lines
    for key in selected_stocks:
        fig.add_trace(
            create_trace(
                x=filtered_stocks["year"],
                y=normalised_stocks[key],
                label=key.split("_")[0],
                mode="lines",
                line_dash="dash",
            )
        )
    # Add fares as step lines
    for key in selected_fares:
        fig.add_trace(
            create_trace(
                x=filtered_fares["year"],
                y=normalised_fares[key],
                label=key,
                line_shape="hv",
            )
        )
    layout = create_layout(
        title="Transportation Costs in the UK vs Global Stock Indices<br><sup>Prices are normalised to the same starting point of 1</sup>"
    )
    fig.update_layout(layout)
    return fig


def create_trace(
    x, y, label: str, mode=LINE_AND_MARKER, line_shape=None, line_dash=None
) -> go.Scatter:
    return go.Scatter(
        x=x, y=y, mode=mode, name=label, line_shape=line_shape, line_dash=line_dash
    )


def create_layout(title: str, type=None):
    return dict(
        title=title,
        width=960,
        height=500,
        xaxis=dict(
            showgrid=False, linecolor="#7f7f7f", linewidth=2, ticks="outside", type=type
        ),
        showlegend=True,
        plot_bgcolor="white",
    )


def normalise_df_to_first_value_per_col(df):
    normed = df.copy()
    for col in normed.columns:
        if col != "year":
            normed[col] = normalise_series_to_first_value(normed[col])
    return normed


def normalise_series_to_first_value(df):
    return df / df.dropna().iloc[0]


def normalise_fares_to_stock_anchor(fares_df, stock_normed_df):
    normed = fares_df.copy()
    years = fares_df["year"].values
    for col in normed.columns:
        if col != "year":
            normed[col] = normalise_series_to_stock_anchor(
                normed[col], stock_normed_df, years
            )
    return normed


def normalise_series_to_stock_anchor(series, stock_normed_df, years):
    """Normalises fare series such that its first valid point gets set to the
    highest equivalent in the corresponding year of the stocks DataFrame."""
    mask = ~series.isna()
    if mask.any():
        first_label = mask.idxmax()
        first_pos = series.index.get_loc(first_label)
        fare_start_year = years[first_pos]
        # Find the max normed stock value for that year
        if fare_start_year in stock_normed_df["year"].values:
            anchor = (
                stock_normed_df.loc[stock_normed_df["year"] == fare_start_year]
                .drop("year", axis=1)
                .max(axis=1)
                .iloc[0]
            )
        else:
            anchor = 1.0  # Fallback if year missing
        anchor_fare = series.iloc[first_pos]
        return (series / anchor_fare) * anchor
    else:
        return series


if __name__ == "__main__":
    init_session_state()
    dashboard()
