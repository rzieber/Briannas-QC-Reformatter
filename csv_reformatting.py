import pickle as pkl
from datetime import timedelta
from pathlib import Path
import warnings

import pandas as pd

from station_config import get_station_config
from weather_station_qc import process_station_dataframe


"""
Populate the station-specific settings in station_config.py before running this script.

Workflow:
1. Match each CSV to a station config.
2. Manually map raw columns to Brianna's canonical column names or descriptive extras.
3. Round timestamps to the nearest minute, convert to UTC, remove duplicate timestamps,
   sort out-of-order timestamps, and fill gaps with NaNs.
4. Save one pickle per station, with `time` as the first data column.
"""

data = Path("")
csv_export = Path("")
pickle_export = Path("")

with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=UserWarning)
    warnings.simplefilter("ignore", category=FutureWarning)

    for csv in data.rglob("*.csv"):
        file_name = str(csv.stem)
        print(f"Processing {file_name}")

        config = get_station_config(file_name)
        if config is None:
            print(f"\tNo station config found for {file_name}. Add one in station_config.py.")
            continue

        df = pd.read_csv(csv, low_memory=False)

        try:
            cleaned_df, audit = process_station_dataframe(
                raw_df=df,
                config=config,
                time_delta=timedelta(minutes=1),
            )
        except Exception as exc:
            print(f"\tSkipped {file_name}: {exc}")
            continue

        csv_export.mkdir(parents=True, exist_ok=True)
        pickle_export.mkdir(parents=True, exist_ok=True)

        cleaned_df.to_csv(csv_export / f"{file_name}.csv", index=False)
        with open(pickle_export / f"{file_name}.pkl", "wb") as handle:
            pkl.dump(cleaned_df, handle)

        print(
            "\tSaved cleaned CSV and pickle. "
            f"Trimmed start/end rows: {audit.rows_trimmed_start}/{audit.rows_trimmed_end}, "
            f"duplicates: {audit.duplicate_timestamps}, "
            f"out-of-order: {audit.out_of_order_timestamps}."
        )
