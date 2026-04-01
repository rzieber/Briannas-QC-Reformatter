from dataclasses import dataclass, field


REQUIRED_COLUMNS = [
    "time",
    "bmp180_tempC",
    "bmp180_station_P",
    "bmp180_SLP_hPa",
    "bmp180_alt",
    "htu21d_tempC",
    "htu21d_relhum",
    "mcp9808_tempC",
    "rain",
    "vis",
    "ir",
    "uv",
    "uvi",
    "wind_dir",
    "wind_speed",
    "bmp280_tempC",
    "bmp280_SLP_hPa",
    "bmp280_station_P",
    "bmp280_alt",
    "bme_tempC",
    "bme_SLP_hPa",
    "bme_station_P",
    "bme_relhum",
    "bme_alt",
]


@dataclass(frozen=True)
class StationMappingConfig:
    station_match: str
    match_mode: str = "contains"
    time_column: str = "time"
    source_timezone: str = "UTC"
    column_mapping: dict[str, str] = field(default_factory=dict)
    drop_columns: tuple[str, ...] = ()
    passthrough_columns: tuple[str, ...] = ()

    def matches(self, station_name: str) -> bool:
        if self.match_mode == "exact":
            return station_name == self.station_match
        if self.match_mode == "startswith":
            return station_name.startswith(self.station_match)
        return self.station_match in station_name


STATION_CONFIGS = [
    StationMappingConfig(
        station_match="FEWSNET",
        column_mapping={
            'rg':'rain', 'rg2':'rain2', 'rgt':'rain_total', 'rgt2':'rain_total2', 'rgp':'rain_previous', 'rgp2':'rain_previous2',
            'bt1':'bmp280_tempC', 'mt1':'mcp9808_tempC', 'bp1':'bmp280_station_P', 'sv1':'vis', 'si1':'ir', 'su1':'uv',
            'ws':'wind_speed', 'wd':'wind_dir', 'st1':'sht31d_tempC', 'sh1':'sht31d_relhum'
        },
        drop_columns=('wd_compass_dir', 'wg', 'wgd', 'wgd_compass_dir', 'hth', 'hi', 'wbt', 'wbgt', 'bcs', 'css'),
        passthrough_columns=('time',),
    ),
    StationMappingConfig(
        station_match="marshall",
        column_mapping={}, # already mostly reformatted from log -> csv conversion
        drop_columns=('Unnamed: 0', 'index'),
        passthrough_columns=(
            'time','rain','wind_speed','wind_dir','bmp280_station_P','bmp280_tempC','bme_relhum','htu21d_relhum',
            'htu21d_tempC','vis','ir','uv','mcp9808_tempC','bmp180_alt','bmp280_SLP_hPa','bme_tempC','bme_alt',
            'bme_station_P','bmp180_station_P','bmp280_alt','bme_SLP_hPa','bmp180_tempC','bmp180_SLP_hPa', 'uvi'),
    ),
    StationMappingConfig(
        station_match="station-4",
        column_mapping={
            'rg':'rain', 'rgt':'rain_total', 'rgp':'rain_previous', 'ws':'wind_speed', 'wd':'wind_dir', 'bp1':'bmp280_station_P',
            'bt1':'bmp280_tempC', 'bh1':'bmp280_relhum', 'st1':'sht31d_tempC', 'sh1':'sht31d_relhum', 'mt1':'mcp9808_tempC',
            'sv1':'vis', 'si1':'ir', 'su1':'uv', 'lx':'uvi'
        },
        drop_columns=('css', 'hth', 'bcs', 'bpc', 'cfr', 'wg', 'wgd', 'hi', 'wbt', 'wbgt'),
        passthrough_columns=('time',),
    ),
    StationMappingConfig(
        station_match="station-71",
        column_mapping={
            'rg':'rain', 'rgs':'rain_gauge_seconds', 'ws':'wind_speed', 'wd':'wind_dir', 'bp1':'bmp390_station_P',
            'bt1':'bmp390_tempC', 'bh1':'bmp390_relhum', 'bp2':'bmp390_station_P_2', 'bt2':'bmp390_tempC_2', 'bh2':'bmp390_relhum_2',
            'sv1':'vis', 'si1':'ir', 'su1':'uv', 'mt1':'mcp9808_tempC', 'mt2':'mcp9808_tempC_2', 'rgt':'rain_total', 'rgp':'rain_previous',
            'hh1':'htu21d_relhum', 'ht1':'htu21d_tempC', 'ht2':'htu21d_tempC_2', 'hh2':'htu21d_relhum_2', 'lx':'uvi', 
            'st1':'sht31d_tempC', 'sh1':'sht31d_relhum', 'st2':'sht31d_tempC_2', 'sh2':'sht31d_relhum_2'
        },
        drop_columns=(
            'css', 'hth', 'bcs', 'bpc', 'cfr', 'wg', 'wgd', 'vlx', 'hi', 'wbt', 'wbgt', 'tmsms1', 'tmsms2', 'tmsms3', 'tmsms4',
            'tmsmt1', 'tmsmt2', 'blx', 'tlww', 'tlwt', 'tsme25', 'tsmec', 'tsmvwc', 'tsmt', 'pm1s10', 'pm1s25', 'pm1s100',
            'pm1e10', 'pm1e25', 'pm1e100'
        ),
        passthrough_columns=('time',),
    ),
    StationMappingConfig(
        station_match="Trinidad",
        match_mode="startswith",
        column_mapping={
            'bt1':'bmp280_tempC', 'mt1':'mcp9808_tempC', 'ht1':'htu21d_tempC', 'bp1':'bmp280_station_P', 'bh1':'bmp280_relhum',
            'hh1':'htu21d_relhum', 'ws':'wind_speed', 'wd':'wind_dir', 'rg':'rain', 'sv1':'vis', 'si1':'ir', 'su1':'uv',
            'st1':'sht31d_tempC', 'sh1':'sht31d_relhum'
        },
        drop_columns=('wg', 'wgd', 'bcs', 'bpc', 'cfr', 'css', 'hth', 'wd_compass_dir', 'wgd_compass_dir', 'hi', 'wbt', 'wbgt'),
        passthrough_columns=('time',),
    ),
]


def get_station_config(station_name: str) -> StationMappingConfig | None:
    for config in STATION_CONFIGS:
        if config.matches(station_name):
            return config
    return None
