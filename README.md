# Summary
This is a codebase used to reformat 3D-PAWS data collected from the Particle datalogger 
by renaming columns to a specific convention for use in Brianna's QC procedure. <br>
<br>
The columns necessary for Brianna's QC are as follows:
  - time
  - bmp180_tempC
  - bmp180_station_P
  - bmp180_SLP_hPa
  - bmp180_alt
  - htu21d_tempC
  - htu21d_relhum
  - mcp9808_tempC
  - rain
  - vis
  - ir
  - uv
  - uvi
  - wind_dir
  - wind_speed
  - bmp280_tempC
  - bmp280_SLP_hPa
  - bmp280_station_P
  - bmp280_alt
  - bme_tempC
  - bme_SLP_hPa
  - bme_station_P
  - bme_relhum
  - bme_alt
<br>
After reformatting the csv's, a pickle file is created for easier ingest. Finally, statistics can be computed
to assess sensor and station performance. <br>
<br>
NOTE: The above columns must be present. If any of the above are not used by the 3D-PAWS instrument, the column
is included and filled with `np.nan` values. For sensors used by the 3D-PAWS instrument which are NOT present
in the above list, those columns are aptly named and included with their original observations.

# Usage
1. Gather csv's. The `daily_logs_to_csv.py` script may be necessary to convert `.log` files into `.csv`.
2. Apply station mappings in `station_config.py`.
3. Run `csv_reformatting.py` after linking to data input and output folders. See `pickle_creation_example.py` for logic on pickle creation.
4. Run `stats.py` to calculate statistical summary for each sensor and each station. Also performs basic qc as outlined in `weather_station_qc.py`.

# Statistical Calculations
The following properties are calculated by `stats.py`:
  - sensor summary
    - number of valid observations `sensor_valid_obs` (non-null, non-empty)
    - number of expected observations `sensor_expected_obs` (perfect performance)
    - percent of time the sensor was online and operational `sensor_uptime_percent`
  - station summary
    - number of rows in raw csv `rows_in_raw_file`
    - number of rows trimmed from the start `rows_trimmed_start` (rows containing only nulls or only empty)
    - number of rows trimmed from the end `rows_trimmed_end` (rows containing only nulls or only empty)
    - number of rows trimmed total `rows_trimmed_total`
    - number of duplicate timestamps `duplicate_timestamps`
    - number of timestamps out of order `out_of_order_timestamps`
    - number of valid rows `instrument_valid_rows` (non-null, non-empty)
    - number of expected rows `instrument_expected_rows` (perfect performance)
    - percent of time the instrument was online and operational `instrument_uptime_percent`
    - number of minutes in the data period `data_period_minutes`
