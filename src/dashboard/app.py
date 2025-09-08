import streamlit as st
import datetime

def selectors() -> None:
    # Define min and max dates with a slider
    col1, col2 = st.columns(2)

    start_year, end_year = st.slider(
        "Select year range",
        1980, 2025,
        (2010, 2025)
    )
    
    # Two multiselects side by side below slider
    col1, col2 = st.columns(2)
    
    with col1:
        indices = st.multiselect(
            "Select stock indices",
            options=["FTSE100", "S&P 500", "DAX", "Nikkei 225", "Hang Seng"],
            default=["FTSE100"]
        )
    
    with col2:
        transport_modes = st.multiselect(
            "Select transportation modes",
            options=["Tube", "Bus and Coach", "Train"],
            default=["Tube"]
        )

def dashboard() -> None:
    st.write("Welcome.")
    st.write("This interactive dashboard compares transportation costs in the UK with global stock indices.")
    selectors()

if __name__ == "__main__":
    dashboard()