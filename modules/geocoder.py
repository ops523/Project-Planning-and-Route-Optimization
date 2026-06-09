import pandas as pd
import requests
import time
import os

CACHE_FILE = "cache/coordinates_cache.xlsx"

USER_AGENT = "AdwallzBankPlanner/1.0"


# --------------------------------------------------
# Cache Functions
# --------------------------------------------------

def load_cache():

    os.makedirs("cache", exist_ok=True)

    if os.path.exists(CACHE_FILE):
        return pd.read_excel(CACHE_FILE)

    return pd.DataFrame(
        columns=[
            "Address",
            "Latitude",
            "Longitude",
            "Matched_Location"
        ]
    )


def save_cache(cache_df):

    os.makedirs("cache", exist_ok=True)

    cache_df.to_excel(
        CACHE_FILE,
        index=False
    )


# --------------------------------------------------
# Nominatim Search
# --------------------------------------------------

def nominatim_search(address):

    url = "https://nominatim.openstreetmap.org/search"

    headers = {
        "User-Agent": USER_AGENT
    }

    params = {
        "q": address,
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

                    "Latitude":
                        float(data[0]["lat"]),

                    "Longitude":
                        float(data[0]["lon"]),

                    "Matched_Location":
                        data[0]["display_name"]
                }

    except Exception as e:

        print(e)

    return {

        "Latitude": None,

        "Longitude": None,

        "Matched_Location": "NOT FOUND"
    }


# --------------------------------------------------
# Main Function
# --------------------------------------------------

def geocode_dataframe(
    df,
    progress_bar=None,
    status_text=None
):

    cache_df = load_cache()

    results = []

    total = len(df)

    found_count = 0
    not_found_count = 0

    for index, row in df.iterrows():

        address = str(
            row["Address"]
        ).strip()

        # ----------------------------------
        # Check Cache
        # ----------------------------------

        cached = cache_df[
            cache_df["Address"]
            ==
            address
        ]

        if len(cached) > 0:

            lat = cached.iloc[0]["Latitude"]

            lon = cached.iloc[0]["Longitude"]

            matched = cached.iloc[0][
                "Matched_Location"
            ]

        else:

            result = nominatim_search(
                address
            )

            lat = result["Latitude"]

            lon = result["Longitude"]

            matched = result[
                "Matched_Location"
            ]

            cache_df.loc[
                len(cache_df)
            ] = [

                address,

                lat,

                lon,

                matched
            ]

            # Respect Nominatim Rate Limit
            time.sleep(1)

        # ----------------------------------
        # Stats
        # ----------------------------------

        if lat is not None:
            found_count += 1
        else:
            not_found_count += 1

        results.append({

            "Address":
                address,

            "Latitude":
                lat,

            "Longitude":
                lon,

            "Matched_Location":
                matched
        })

        # ----------------------------------
        # Progress
        # ----------------------------------

        percent = (
            index + 1
        ) / total

        if progress_bar:

            progress_bar.progress(
                percent,
                text=f"{round(percent*100,1)}% Complete"
            )

        if status_text:

            status_text.markdown(
                f"""
### Geocoding Progress

**Processed:** {index+1}/{total}

✅ Found: {found_count}

❌ Not Found: {not_found_count}

**Current Address:**

{address[:120]}...
"""
            )

    save_cache(cache_df)

    return pd.DataFrame(
        results
    )
