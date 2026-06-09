import streamlit as st
import pandas as pd
from io import BytesIO

from modules.geocoder import (
    geocode_dataframe
)

st.set_page_config(
    page_title="AU Bank Geocoder",
    layout="wide"
)

st.title(
    "🏦 AU Bank Address Geocoder"
)

uploaded_file = st.file_uploader(
    "Upload Excel",
    type=["xlsx"]
)

if uploaded_file:

    df = pd.read_excel(
        uploaded_file
    )

    st.subheader(
        "Preview"
    )

    st.dataframe(
        df.head()
    )

    if "Address" not in df.columns:

        st.error(
            "Excel must contain Address column"
        )

        st.stop()

    st.success(
        f"{len(df)} addresses loaded"
    )

    if st.button(
        "🚀 Start Geocoding"
    ):

        progress_bar = st.progress(
            0
        )

        status_text = st.empty()

        result_df = geocode_dataframe(
            df,
            progress_bar,
            status_text
        )

        st.success(
            "Geocoding Completed"
        )

        found = result_df[
            result_df["Latitude"]
            .notna()
        ]

        not_found = result_df[
            result_df["Latitude"]
            .isna()
        ]

        c1, c2 = st.columns(2)

        with c1:

            st.metric(
                "Found",
                len(found)
            )

        with c2:

            st.metric(
                "Not Found",
                len(not_found)
            )

        st.dataframe(
            result_df,
            use_container_width=True
        )

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="xlsxwriter"
        ) as writer:

            result_df.to_excel(
                writer,
                sheet_name="Coordinates",
                index=False
            )

        st.download_button(
            "📥 Download Coordinates",
            data=output.getvalue(),
            file_name="au_bank_coordinates.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
