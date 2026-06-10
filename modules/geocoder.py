import pandas as pd
import re


def extract_pincode(address):

    match = re.search(
        r"\b\d{6}\b",
        str(address)
    )

    if match:
        return match.group()

    return None


def geocode_dataframe(
    df,
    progress_bar=None,
    status_text=None
):

    pincode_df = pd.read_csv(
        "data/india_pincodes.csv",
        dtype=str
    )

    pincode_df["Latitude"] = (
        pincode_df["Latitude"]
        .astype(float)
    )

    pincode_df["Longitude"] = (
        pincode_df["Longitude"]
        .astype(float)
    )

    results = []

    total = len(df)

    found = 0
    not_found = 0

    for index, row in df.iterrows():

        address = str(
            row["Address"]
        )

        pincode = extract_pincode(
            address
        )

        lat = None
        lon = None

        if pincode:

            match = pincode_df[
                pincode_df["Pincode"]
                ==
                pincode
            ]

            if len(match):

                lat = float(
                    match.iloc[0]["Latitude"]
                )

                lon = float(
                    match.iloc[0]["Longitude"]
                )

                found += 1

            else:

                not_found += 1

        else:

            not_found += 1

        results.append({

            "Address":
                address,

            "Pincode":
                pincode,

            "Latitude":
                lat,

            "Longitude":
                lon
        })

        percent = (
            index + 1
        ) / total

        if progress_bar:

            progress_bar.progress(
                percent,
                text=f"{round(percent*100,1)}%"
            )

        if status_text:

            status_text.markdown(
                f"""
Processed:
{index+1}/{total}

Found:
{found}

Not Found:
{not_found}
"""
            )

    return pd.DataFrame(
        results
    )
