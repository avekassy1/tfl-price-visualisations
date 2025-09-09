import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
import pandas as pd

from src.utils import LINE_AND_MARKER


def intro_text():
    st.title("Fares & Shares: Tracking UK Transport Costs vs Markets")
    st.markdown(
        """
        This interactive dashboard compares transportation costs in the UK with well-known stock indices.<br><br>
        **Data sources**

        - [ONS Bus & Coach Fares RPI](https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/docx/mm23)
        - [ONS Train Fares RPI](https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/docw/mm23)
        - [Wall Street Journal Markets](https://www.wsj.com/finance)
        - TfL Fares: collated by moi with 🫶
        
        **Methodology**

        Prices are normalised to the same starting point of 1. In case of initial missing values, the highest stock price in the first entry's year is used as a starting point.
        <br><br>
        """,
        unsafe_allow_html=True,
    )


def selectors():
    # Define min and max dates with a slider

    start_year, end_year = st.slider("Select year range", 2000, 2025, (2010, 2025))
    st.session_state.start_year, st.session_state.end_year = start_year, end_year

    selected_stocks = st.multiselect(
        "Select stock indices",
        options=[
            stock
            for stock in st.session_state.combined_stocks.columns.to_list()
            if stock != "year"
        ],
        default=["FTSE100"],
    )
    st.session_state.selected_stocks = selected_stocks

    selected_transport_modes = st.multiselect(
        "Select transportation modes",
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


def dashboard() -> None:
    col_pad_left, col_left, col_mid, col_mid2, col_right, col_pad_right = st.columns(
        [0.1, 5, 0.1, 0.1, 3, 1]
    )
    with col_right:
        selectors()
    # Vertical divider as HTML in a separate column
    with col_mid:
        st.markdown(
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


############## UTILS ##############
# TODO - move members to utils.py


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
                label=key.replace("_", " "),
                line_shape="hv",
            )
        )
    layout = create_layout()
    fig.update_yaxes(title_text="Relative price")
    fig.update_xaxes(title_text="Year", rangeselector_font_color="#000000")
    fig.update_layout(layout)
    return fig


def create_trace(
    x, y, label: str, mode=LINE_AND_MARKER, line_shape=None, line_dash=None
) -> go.Scatter:
    return go.Scatter(
        x=x, y=y, mode=mode, name=label, line_shape=line_shape, line_dash=line_dash
    )


def create_layout(title: str = None, type=None):
    return dict(
        width=960,
        height=400,
        font=dict(
            family="sans-serif",
            color="#31333F",
            size=16,
        ),
        xaxis=dict(
            showgrid=False,
            linecolor="#7f7f7f",
            linewidth=2,
            ticks="outside",
            title="Year",
            tickfont=dict(color="#7f7f7f"),
            # titlefont=dict(color="#31333F"),
            type=type,
        ),
        yaxis=dict(
            #     showgrid=False,
            #     linecolor="#31333F",
            #     linewidth=2,
            tickfont=dict(color="#7f7f7f"),
            # titlefont=dict(color="#31333F"),
        ),
        showlegend=True,
        legend=dict(x=0.1, y=1.0),
        # modebar=dict(x=0, y=1),
        plot_bgcolor="#fdfdf8",
        paper_bgcolor="#fdfdf8",
        margin=dict(t=20, r=20, b=40, l=40),
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
    intro_text()
    dashboard()
