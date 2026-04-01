# Refactor Summary

## What Changed

The codebase was refactored so that station-specific column mapping is now separate from the shared QC and statistics logic.

The main correction is that Brianna's required columns are treated as the required base schema, not the only allowed schema. Extra sensors can now remain in the output as long as they use descriptive names.

## New Structure

### `station_config.py`

This file now holds the manual mapping framework you asked for.

Each station config includes:

- `column_mapping`: map raw CSV column names to Brianna's canonical names or your own descriptive extra-sensor names
- `drop_columns`: raw columns to remove
- `passthrough_columns`: columns that are already named well enough and should be preserved as-is
- `time_column`: lets you specify the raw timestamp column name if it is not already called `time`
- `source_timezone`: lets you define the timezone before conversion to UTC

I left the actual mappings blank for you to fill in manually.

### `weather_station_qc.py`

This is the shared processing module.

It now handles:

- parsing timestamps
- converting timestamps to UTC
- rounding timestamps to the nearest minute
- trimming empty or invalid rows from the start and end of the instrument record
- counting and removing duplicate timestamps
- counting out-of-order timestamps
- sorting timestamps into chronological order
- filling missing timestamps with `NaN` rows
- ensuring Brianna's required columns exist
- calculating per-sensor valid observations, expected observations, and sensor uptime
- calculating instrument uptime

## Updated Scripts

### `csv_reformatting.py`

This script now:

- reads raw CSV files
- looks up the matching station config
- applies your manual mapping rules
- runs the shared QC/minute-formatting pipeline
- exports a cleaned CSV
- exports one pickle file per station

### `stats.py`

This script now:

- reads the raw CSV files by default so duplicate and out-of-order timestamp statistics are preserved
- runs the same shared QC pipeline as the reformatter
- exports:
  - cleaned station CSVs
  - `*_sensor_summary.csv`
  - `*_station_summary.csv`

## Important Behavior Changes

- Required Brianna columns are always created if missing and filled with `np.nan`
- Extra sensors are preserved instead of being incorrectly forced into Brianna's canonical names
- The scripts now raise a clear error when raw columns have not yet been classified into mapping, drop, or passthrough
- Sensor uptime is now calculated per column after trimming invalid values from that column's start and end
- Instrument uptime is calculated separately using row-level validity

## Validation

The updated scripts were checked with:

```bash
python3 -m py_compile csv_reformatting.py stats.py station_config.py weather_station_qc.py _fill_time_gaps.py
```

## Next Step

Fill in the station entries in `station_config.py`, then run the pipeline on one station first to confirm the mapping and summary outputs match Brianna's QC expectations.
