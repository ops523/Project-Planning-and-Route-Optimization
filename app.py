import streamlit as st
import pandas as pd
from io import BytesIO

from modules.geocoder import geocode_dataframe

# --------------------------------------------------
# Page Config
# --------------------------------------------------

st.set_page_config(
    page_title="AU Bank Branch Geocoder",
    layout="wide"
)

# --------------------------------------------------
# Title
# --------------------------------------------------

st.title("🏦 AU Bank Branch Geocoder")

st.markdown("""
Upload an Excel file containing:

- Branch
- Pincode
- City
- State

The system will:

✅ Search AU Small Finance Bank branches

✅ Validate results

✅ Cache coordinates

✅ Generate Latitude & Longitude
""")

# --------------------------------------------------
# Upload File
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

# --------------------------------------------------
# Process File
# --------------------------------------------------

if uploaded_file:

    try:

        df = pd.read_excel(uploaded_file)

        st.subheader("Excel Preview")

        st.dataframe(df.head())

        st.write("Columns Found:")

        st.code(df.columns.tolist())

        required_columns = [
            "Branch",
            "Pincode",
            "City",
            "State"
        ]

        missing = [
            col
            for col in required_columns
            if col not in df.columns
        ]

        if missing:

            st.error(
                f"Missing columns: {missing}"
            )

            st.stop()

        st.success(
            f"{len(df)} branches found"
        )

        # ------------------------------------------
        # Start Button
        # ------------------------------------------

        if st.button("🚀 Start Geocoding"):

            with st.spinner(
                "Fetching coordinates..."
            ):

                result_df = geocode_dataframe(
                    df
                )

            st.success(
                "Geocoding Completed"
            )

            # --------------------------------------
            # Results
            # --------------------------------------

            st.subheader(
                "Results"
            )

            st.dataframe(
                result_df,
                use_container_width=True
            )

            # --------------------------------------
            # Stats
            # --------------------------------------

            found = result_df[
                result_df["Latitude"]
                .notna()
            ]

            not_found = result_df[
                result_df["Latitude"]
                .isna()
            ]

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Found",
                    len(found)
                )

            with col2:
                st.metric(
                    "Not Found",
                    len(not_found)
                )

            # --------------------------------------
            # Download Excel
            # --------------------------------------

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
                label="📥 Download Coordinates",
                data=output.getvalue(),
                file_name="au_bank_coordinates.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:

        st.error(str(e))
