import os
import sys
import warnings
import pandas as pd
from datetime import timedelta
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from station_config import get_station_config
from weather_station_qc import calculate_sensor_statistics, process_station_dataframe

def main(data=None, report=None, time_delta=timedelta(minutes=1), plots=None):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)

        csv_files = list(data.glob("*.csv")) 

        for csv in csv_files:
            folder_name = str(csv.stem)
            print(f"Processing statistics for {folder_name}.")

            config = get_station_config(folder_name)
            if config is None:
                print(f"\tNo station config found for {folder_name}. Add one in station_config.py.")
                continue

            raw_df = pd.read_csv(csv, low_memory=False)

            try:
                cleaned_df, audit = process_station_dataframe(raw_df, config, time_delta=time_delta)
            except Exception as exc:
                print(f"\tSkipped {folder_name}: {exc}")
                continue

            sensor_summary_df = calculate_sensor_statistics(cleaned_df)
            station_summary_df = pd.DataFrame(
                [
                    {
                        "station": folder_name,
                        "rows_in_raw_file": audit.rows_in_raw_file,
                        "rows_trimmed_start": audit.rows_trimmed_start,
                        "rows_trimmed_end": audit.rows_trimmed_end,
                        "rows_trimmed_total": audit.rows_trimmed_start + audit.rows_trimmed_end,
                        "duplicate_timestamps": audit.duplicate_timestamps,
                        "out_of_order_timestamps": audit.out_of_order_timestamps,
                        "instrument_valid_rows": audit.instrument_valid_rows,
                        "instrument_expected_rows": audit.instrument_expected_rows,
                        "instrument_uptime_percent": audit.instrument_uptime_percent,
                        "data_period_minutes": audit.rows_after_gap_fill,
                    }
                ]
            )

            try:
                os.makedirs(report / folder_name, exist_ok=True)
            except Exception:
                print("Could not create the directory:", report / folder_name)

            cleaned_df.to_csv(report / folder_name / f"{folder_name}_cleaned.csv", index=False)
            sensor_summary_df.to_csv(report / folder_name / f"{folder_name}_sensor_summary.csv", index=False)
            station_summary_df.to_csv(report / folder_name / f"{folder_name}_station_summary.csv", index=False)
        
        print("Process completed ---------------------------------------------------------\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        main(
            Path(""),           # csv's (NOT REFORMATTED, the column mapping is used here)
            Path(""),           # output
            timedelta(minutes=1)
        )
    else:
        if len(sys.argv) == 4: main(Path(sys.argv[1]), Path(sys.argv[2]), timedelta(minutes=int(sys.argv[3])))
        if len(sys.argv) == 5: main(Path(sys.argv[1]), Path(sys.argv[2]), timedelta(minutes=int(sys.argv[3])), Path(sys.argv[4]))
