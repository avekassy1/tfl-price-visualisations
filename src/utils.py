import plotly.graph_objects as go


LINE_AND_MARKER = "lines+markers"

############## PLOTTING ##############
def comparison_plot(combined_stocks, combined_fares, selected_fares, selected_stocks, start_year, end_year):
    filtered_stocks = combined_stocks.loc[
        (combined_stocks.year >= start_year) & (combined_stocks.year <= end_year)
    ]
    filtered_fares = combined_fares.loc[
        (combined_fares.year >= start_year) & (combined_fares.year <= end_year)
    ]
    normalised_stocks = normalise_df_to_first_value_per_col(filtered_stocks)
    normalised_fares = normalise_fares_to_stock_anchor(
        filtered_fares, normalised_stocks[selected_stocks + ["year"]]
    )

    fig = go.Figure()
    # Add stock indices as dashed lines
    for key in selected_stocks:
        fig.add_trace(
            create_trace(
                x=filtered_stocks["year"],
                y=normalised_stocks[key] * 100,
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
                y=normalised_fares[key] * 100,
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
        legend=dict(x=1, y=0.5),
        # modebar=dict(x=0, y=1),
        plot_bgcolor="#fdfdf8",
        paper_bgcolor="#fdfdf8",
        margin=dict(t=20, r=20, b=40, l=40),
    )

############## DATA PROCESSING ##############
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