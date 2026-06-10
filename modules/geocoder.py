import pandas as pd
import requests
import time
import os
import re

CACHE_FILE = "cache/coordinates_cache.xlsx"

USER_AGENT = "AdwallzBankPlanner/1.0 (contact@adwallz.com)"


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
# Address Cleaning
# --------------------------------------------------

def clean_address(address):

    address = str(address)

    address = address.replace("\n", " ")
    address = address.replace("#", " ")
    address = address.replace("-", " ")
    address = address.replace("|", " ")

    address = re.sub(r"\s+", " ", address)

    return address.strip()


# --------------------------------------------------
# Extract Pincode
# --------------------------------------------------

def extract_pincode(address):

    match = re.search(
        r"\b\d{6}\b",
        str(address)
    )

    if match:
        return match.group()

    return None


# --------------------------------------------------
# Nominatim Search
# --------------------------------------------------

def nominatim_query(query):

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

        if response.status_code != 200:

            return None

        data = response.json()

        if len(data) == 0:

            return None

        return {

            "Latitude":
                float(data[0]["lat"]),

            "Longitude":
                float(data[0]["lon"]),

            "Matched_Location":
                data[0]["display_name"]
        }

    except Exception:

        return None


# --------------------------------------------------
# Search Logic
# --------------------------------------------------

def geocode_address(address):

    cleaned = clean_address(address)

    pincode = extract_pincode(cleaned)

    queries = []

    # Priority 1
    if pincode:
        queries.append(
            f"{pincode} India"
        )

    # Priority 2
    queries.append(cleaned)

    # Priority 3
    parts = cleaned.split(",")

    if len(parts) >= 3:

        queries.append(
            ",".join(parts[-3:])
        )

    # Try all searches
    for query in queries:

        result = nominatim_query(query)

        if result:

            return result

        time.sleep(1)

    return {

        "Latitude": None,

        "Longitude": None,

        "Matched_Location": "NO RESULT"
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

            result = geocode_address(
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

        if pd.notna(lat):

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

        # Progress Bar
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

Processed: **{index+1}/{total}**

✅ Found: **{found_count}**

❌ Not Found: **{not_found_count}**

Current Address:

{address[:150]}
"""
            )

    save_cache(cache_df)

    return pd.DataFrame(results)
