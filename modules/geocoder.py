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
            "Branch",
            "Pincode",
            "Latitude",
            "Longitude",
            "Display_Name"
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

def nominatim_search(query):

    url = "https://nominatim.openstreetmap.org/search"

    headers = {
        "User-Agent": USER_AGENT
    }

    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 5,
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
            return response.json()

    except Exception as e:
        print(e)

    return []


# --------------------------------------------------
# Validation
# --------------------------------------------------

def is_au_bank_result(result):

    display_name = str(
        result.get("display_name", "")
    ).lower()

    keywords = [
        "au small finance bank",
        "au bank",
        "au finance bank"
    ]

    return any(
        k in display_name
        for k in keywords
    )


def pincode_matches(
    result,
    target_pincode
):

    if not target_pincode:
        return True

    display_name = str(
        result.get("display_name", "")
    )

    return str(target_pincode) in display_name


def find_best_result(
    results,
    pincode
):

    for result in results:

        if (
            is_au_bank_result(result)
            and
            pincode_matches(
                result,
                pincode
            )
        ):
            return result

    for result in results:

        if is_au_bank_result(result):
            return result

    return None


# --------------------------------------------------
# Branch Search
# --------------------------------------------------

def geocode_branch(
    branch,
    pincode,
    city,
    state
):

    queries = [

        f"AU Small Finance Bank {branch} {pincode} India",

        f"AU Small Finance Bank {city} {pincode} India",

        f"AU Bank {branch} {city} India",

        f"AU Bank {city} {state} India",

        f"{pincode} {city} {state} India"
    ]

    for query in queries:

        results = nominatim_search(
            query
        )

        best = find_best_result(
            results,
            pincode
        )

        if best:

            return {

                "Latitude":
                    float(best["lat"]),

                "Longitude":
                    float(best["lon"]),

                "Display_Name":
                    best["display_name"]
            }

        time.sleep(1.1)

    return {

        "Latitude": None,

        "Longitude": None,

        "Display_Name": "NOT FOUND"
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

        branch = str(
            row["Branch"]
        ).strip()

        pincode = str(
            row["Pincode"]
        ).strip()

        city = str(
            row["City"]
        ).strip()

        state = str(
            row["State"]
        ).strip()

        cached = cache_df[
            (
                cache_df["Branch"]
                ==
                branch
            )
            &
            (
                cache_df["Pincode"]
                .astype(str)
                ==
                pincode
            )
        ]

        if len(cached) > 0:

            lat = cached.iloc[0]["Latitude"]
            lon = cached.iloc[0]["Longitude"]
            display = cached.iloc[0]["Display_Name"]

        else:

            result = geocode_branch(
                branch,
                pincode,
                city,
                state
            )

            lat = result["Latitude"]
            lon = result["Longitude"]
            display = result["Display_Name"]

            cache_df.loc[
                len(cache_df)
            ] = [
                branch,
                pincode,
                lat,
                lon,
                display
            ]

        if lat is not None:
            found_count += 1
        else:
            not_found_count += 1

        results.append({

            "Branch": branch,

            "Pincode": pincode,

            "City": city,

            "State": state,

            "Latitude": lat,

            "Longitude": lon,

            "Matched_Location": display
        })

        # -------------------------
        # Progress Update
        # -------------------------

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
### Processing

**Branch:** {branch}

**Progress:** {index+1}/{total}

✅ Found: {found_count}

❌ Not Found: {not_found_count}
"""
            )

    save_cache(cache_df)

    return pd.DataFrame(results)
