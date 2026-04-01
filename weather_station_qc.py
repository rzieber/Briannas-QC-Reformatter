from dataclasses import dataclass
from datetime import timedelta

import numpy as np
import pandas as pd

from _fill_time_gaps import fill_empty_rows
from station_config import REQUIRED_COLUMNS, StationMappingConfig


INVALID_NUMERIC_VALUES = {-999.99, -1000.0}


@dataclass(frozen=True)
class ProcessingAudit:
    rows_in_raw_file: int
    rows_trimmed_start: int
    rows_trimmed_end: int
    duplicate_timestamps: int
    out_of_order_timestamps: int
    rows_after_gap_fill: int
    instrument_valid_rows: int
    instrument_expected_rows: int
    instrument_uptime_percent: float


def is_invalid_observation(value) -> bool:
    if pd.isna(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return value in INVALID_NUMERIC_VALUES


def get_data_columns(df: pd.DataFrame) -> list[str]:
    return [col for col in df.columns if col != "time"]


def invalid_observation_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df.apply(lambda column: column.map(is_invalid_observation))


def normalize_time_column(series: pd.Series, source_timezone: str) -> pd.Series:
    timestamps = pd.to_datetime(series, errors="coerce")

    if timestamps.dt.tz is None:
        timestamps = timestamps.dt.tz_localize(source_timezone)
    else:
        timestamps = timestamps.dt.tz_convert("UTC")

    return timestamps.dt.tz_convert("UTC").dt.round("min")


def identify_unmapped_columns(raw_columns: list[str], config: StationMappingConfig) -> list[str]:
    allowed = set(REQUIRED_COLUMNS)
    allowed.update(config.column_mapping.keys())
    allowed.update(config.drop_columns)
    allowed.update(config.passthrough_columns)
    allowed.add(config.time_column)
    return [col for col in raw_columns if col not in allowed]


def apply_station_mapping(raw_df: pd.DataFrame, config: StationMappingConfig) -> pd.DataFrame:
    df = raw_df.copy()
    raw_columns = list(df.columns)
    unresolved = identify_unmapped_columns(raw_columns, config)

    if unresolved:
        raise ValueError(
            "Unmapped columns remain. Add them to column_mapping, drop_columns, or "
            f"passthrough_columns in station_config.py: {unresolved}"
        )

    drop_columns = [col for col in config.drop_columns if col in df.columns]
    if drop_columns:
        df = df.drop(columns=drop_columns)

    rename_map = dict(config.column_mapping)
    if config.time_column != "time":
        rename_map[config.time_column] = "time"

    df = df.rename(columns=rename_map)
    df["time"] = normalize_time_column(df["time"], config.source_timezone)
    return df


def ensure_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for column in REQUIRED_COLUMNS:
        if column not in result.columns:
            result[column] = np.nan

    ordered_columns = ["time"]
    ordered_columns.extend([col for col in REQUIRED_COLUMNS if col != "time"])
    extras = [col for col in result.columns if col not in ordered_columns]
    return result[ordered_columns + extras]


def trim_instrument_edges(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    if df.empty:
        return df.copy(), 0, 0

    data_columns = get_data_columns(df)
    if not data_columns:
        return df.copy(), 0, 0

    valid_row_mask = ~invalid_observation_frame(df[data_columns]).all(axis=1)

    if not valid_row_mask.any():
        return df.iloc[0:0].copy(), len(df), 0

    first_valid_position = int(np.flatnonzero(valid_row_mask.to_numpy())[0])
    last_valid_position = int(np.flatnonzero(valid_row_mask.to_numpy())[-1])

    trimmed = df.iloc[first_valid_position:last_valid_position + 1].reset_index(drop=True)
    rows_trimmed_start = first_valid_position
    rows_trimmed_end = len(df) - last_valid_position - 1
    return trimmed, rows_trimmed_start, rows_trimmed_end


def trim_series_edges(series: pd.Series) -> pd.Series:
    valid_mask = ~series.map(is_invalid_observation)
    if not valid_mask.any():
        return series.iloc[0:0]

    first_valid_position = int(np.flatnonzero(valid_mask.to_numpy())[0])
    last_valid_position = int(np.flatnonzero(valid_mask.to_numpy())[-1])
    return series.iloc[first_valid_position:last_valid_position + 1]


def calculate_sensor_statistics(df: pd.DataFrame) -> pd.DataFrame:
    records = []

    for column in get_data_columns(df):
        trimmed_series = trim_series_edges(df[column])
        expected_obs = len(trimmed_series)

        if expected_obs == 0:
            valid_obs = 0
            uptime_percent = np.nan
        else:
            valid_obs = int((~trimmed_series.map(is_invalid_observation)).sum())
            uptime_percent = round((valid_obs / expected_obs) * 100, 1)

        records.append(
            {
                "sensor": column,
                "sensor_valid_obs": valid_obs,
                "sensor_expected_obs": expected_obs,
                "sensor_uptime_percent": uptime_percent,
            }
        )

    return pd.DataFrame(records)


def calculate_instrument_uptime(df: pd.DataFrame) -> tuple[int, int, float]:
    data_columns = get_data_columns(df)
    if not data_columns or df.empty:
        return 0, 0, np.nan

    valid_row_mask = ~invalid_observation_frame(df[data_columns]).all(axis=1)
    expected_rows = len(df)
    valid_rows = int(valid_row_mask.sum())
    uptime_percent = np.nan if expected_rows == 0 else round((valid_rows / expected_rows) * 100, 1)
    return valid_rows, expected_rows, uptime_percent


def process_station_dataframe(
    raw_df: pd.DataFrame,
    config: StationMappingConfig,
    time_delta: timedelta = timedelta(minutes=1),
) -> tuple[pd.DataFrame, ProcessingAudit]:
    mapped = apply_station_mapping(raw_df, config)
    mapped = ensure_required_columns(mapped)
    mapped = mapped.replace("", np.nan)

    trimmed, rows_trimmed_start, rows_trimmed_end = trim_instrument_edges(mapped)

    duplicate_mask = trimmed.duplicated(subset="time", keep="first")
    duplicate_count = int(duplicate_mask.sum())
    without_duplicates = trimmed.loc[~duplicate_mask].copy()

    out_of_order_mask = without_duplicates["time"] < without_duplicates["time"].shift(1)
    out_of_order_count = int(out_of_order_mask.sum())
    ordered = without_duplicates.sort_values("time").reset_index(drop=True)

    gap_filled = fill_empty_rows(ordered, time_delta).reset_index(drop=True)
    gap_filled = ensure_required_columns(gap_filled)

    instrument_valid_rows, instrument_expected_rows, instrument_uptime_percent = calculate_instrument_uptime(gap_filled)

    audit = ProcessingAudit(
        rows_in_raw_file=len(raw_df),
        rows_trimmed_start=rows_trimmed_start,
        rows_trimmed_end=rows_trimmed_end,
        duplicate_timestamps=duplicate_count,
        out_of_order_timestamps=out_of_order_count,
        rows_after_gap_fill=len(gap_filled),
        instrument_valid_rows=instrument_valid_rows,
        instrument_expected_rows=instrument_expected_rows,
        instrument_uptime_percent=instrument_uptime_percent,
    )
    return gap_filled, audit
