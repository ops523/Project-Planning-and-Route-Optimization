import streamlit as st
import pandas as pd
import requests
import time
from io import BytesIO

st.set_page_config(
    page_title="AU Bank Branch Geocoder",
    layout="wide"
)

st.title("🏦 AU Bank Branch Geocoder")

USER_AGENT = "adwallz-bank-route-planner/1.0"

# --------------------------------------------------
# Nominatim Search
# --------------------------------------------------

def nominatim_search(query):

    url = "https://nominatim.openstreetmap.org/search"

    headers = {
        "User-Agent": USER_AGENT
    }

    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:

            data = response.json()

            if len(data) > 0:

                return {
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"]),
                    "display_name": data[0]["display_name"]
                }

    except Exception as e:
        print(e)

    return None


# --------------------------------------------------
# Multi-stage search
# --------------------------------------------------

def geocode_branch(branch, pincode, city, state):

    searches = [

        f"AU Small Finance Bank {branch} {pincode} India",

        f"AU Small Finance Bank {city} {pincode} India",

        f"AU Bank {city} {state} India",

        f"{pincode} {city} {state} India"
    ]

    for q in searches:

        result = nominatim_search(q)

        if result:
            return result

        # Nominatim usage policy
        time.sleep(1.1)

    return None


# --------------------------------------------------
# Cache
# --------------------------------------------------

CACHE_FILE = "coordinate_cache.xlsx"

try:
    cache_df = pd.read_excel(CACHE_FILE)

except:
    cache_df = pd.DataFrame(
        columns=[
            "Branch",
            "Pincode",
            "Latitude",
            "Longitude",
            "Display_Name"
        ]
    )


# --------------------------------------------------
# Upload
# --------------------------------------------------

uploaded = st.file_uploader(
    "Upload Branch Excel",
    type=["xlsx"]
)

if uploaded:

    df = pd.read_excel(uploaded)

    st.write("Preview")
    st.dataframe(df.head())

    if st.button("Start Geocoding"):

        results = []

        progress = st.progress(0)

        total = len(df)

        for idx, row in df.iterrows():

            branch = str(row["Branch"])
            pincode = str(row["Pincode"])
            city = str(row["City"])
            state = str(row["State"])

            cached = cache_df[
                (cache_df["Branch"] == branch)
                &
                (cache_df["Pincode"].astype(str) == pincode)
            ]

            if len(cached) > 0:

                lat = cached.iloc[0]["Latitude"]
                lon = cached.iloc[0]["Longitude"]
                disp = cached.iloc[0]["Display_Name"]

            else:

                result = geocode_branch(
                    branch,
                    pincode,
                    city,
                    state
                )

                if result:

                    lat = result["lat"]
                    lon = result["lon"]
                    disp = result["display_name"]

                    cache_df.loc[len(cache_df)] = [
                        branch,
                        pincode,
                        lat,
                        lon,
                        disp
                    ]

                else:

                    lat = None
                    lon = None
                    disp = "NOT FOUND"

            results.append({
                "Branch": branch,
                "Pincode": pincode,
                "City": city,
                "State": state,
                "Latitude": lat,
                "Longitude": lon,
                "Location": disp
            })

            progress.progress((idx + 1) / total)

        output_df = pd.DataFrame(results)

        # save cache
        cache_df.to_excel(
            CACHE_FILE,
            index=False
        )

        st.success("Completed")

        st.dataframe(output_df)

        output = BytesIO()

        with pd.ExcelWriter(
            output,
            engine="xlsxwriter"
        ) as writer:

            output_df.to_excel(
                writer,
                sheet_name="Coordinates",
                index=False
            )

        st.download_button(
            "Download Coordinates",
            output.getvalue(),
            file_name="au_bank_coordinates.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
