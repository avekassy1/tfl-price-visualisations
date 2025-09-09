import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
import pandas as pd
import os, sys

sys.path.append(str(Path(__file__).resolve().parents[2]))
from src.utils import LINE_AND_MARKER, comparison_plot


def intro_text():
    st.title("Fares & Shares: Tracking UK Transport Costs vs Markets")
    st.write("")
    col_left, col_mid, col_mid2, col_right, col_pad_right = st.columns(
        [5.5, 0.1, 0.1, 3, 1]
    )
    with col_left:
        st.markdown(
        f"""
        This interactive dashboard compares transportation costs in the UK with well-known stock indices. You can select a start and end year between 2000 and 2025, 
        and choose from {st.session_state.combined_fares.shape[1] - 1} transportation modes (step lines) and {st.session_state.combined_stocks.shape[1] - 1} stock 
        indeces (dashed lines).<br><br> 
        **Data sources**  
        - [ONS Bus & Coach Fares RPI](https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/docx/mm23)
        - [ONS Train Fares RPI](https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/docw/mm23)
        - [Wall Street Journal Market Data](https://www.wsj.com/market-data)
        - TfL Fares: collected by me with ❤️

        **Methodology**  
        Prices are normalised to the same starting point of 100. In case of initial missing values (increased fares for peak hours, for example, 
        were introduced in 2008), the highest stock price in the first entry's year is used as a starting point. The idea is to provide a fair comparison for evaluating
        the financial returns of a hypothetical investment.
        """,
        unsafe_allow_html=True,)
    with col_right:
        st.image(DATA_DIR / "sadiq-get-real.png", caption=" ")
    st.write("")


def selectors():
    # Define min and max dates with a slider
    st.subheader("Selectors")
    start_year, end_year = st.slider("Year range", 2000, 2025, (2010, 2024))
    st.session_state.start_year, st.session_state.end_year = start_year, end_year

    selected_stocks = st.multiselect(
        "Stock indices",
        options=[
            stock
            for stock in st.session_state.combined_stocks.columns.to_list()
            if stock != "year"
        ],
        default=["FTSE100"],
    )
    st.session_state.selected_stocks = selected_stocks

    selected_transport_modes = st.multiselect(
        "Transportation modes",
        options=[
            str(mode).replace("_", " ")
            for mode in st.session_state.combined_fares.columns.to_list()
            if mode != "year"
        ],
        default=[
            "Single Z1 to Z4 Oyster Peak",
            "Bus and Coach",
            "Rail",
        ],  # TODO - add (Nationwide) and (TfL) flags
    )
    st.session_state.selected_transport_modes = [
        mode.replace(" ", "_") for mode in selected_transport_modes
    ]


def contruct_plot():
    if st.session_state.selected_stocks and st.session_state.selected_transport_modes:
        fig = comparison_plot(
            combined_stocks=st.session_state.combined_stocks,
            combined_fares=st.session_state.combined_fares,
            selected_fares=st.session_state.selected_transport_modes,
            selected_stocks=st.session_state.selected_stocks,
            start_year=st.session_state.start_year,
            end_year=st.session_state.end_year,
        )
        st.plotly_chart(fig, use_container_width=False)
    else:
        st.info(
            "Please select at least one stock index and one transportation mode to display the graph."
        )

def vertical_divider_line():
    return st.markdown(
            """
        <div style="
            height: 350px;
            display: flex;
            justify-content: center;
            align-items: center;
        ">
            <div style="
                border-left: 2px solid #7f7f7f;
                height: 80%;
            "></div>
        </div>
        """,
            unsafe_allow_html=True,
        )

def dashboard() -> None:
    col_left, col_mid, col_mid2, col_right, col_pad_right = st.columns(
        [5.5, 0.1, 0.1, 3, 1]
    )
    with col_right:
        selectors()
    # with col_mid:
        # vertical_divider_line()
    with col_left:
        # Render the plot if there is at least one selection in each category
        contruct_plot()

############## DATA ##############
DATA_DIR = Path(__file__).parents[2] / "data"
FARE_PRICES_DIR = DATA_DIR / "fares"
STOCK_PRICES_DIR = DATA_DIR / "stocks"

def init_session_state() -> None:
    st.set_page_config(layout="wide")
    if "combined_fares" not in st.session_state:
        st.session_state.combined_fares = pd.read_csv(
            FARE_PRICES_DIR / "processed" / "combined_transport_fares.csv"
        )

    if "combined_stocks" not in st.session_state:
        st.session_state.combined_stocks = pd.read_csv(
            STOCK_PRICES_DIR / "combined_indices.csv"
        )


if __name__ == "__main__":
    init_session_state()
    intro_text()
    dashboard()
