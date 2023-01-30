import datetime

import cdsapi

from moisture_tracers.era5 import datadir

c = cdsapi.Client()

variables_2d = [
    "surface_pressure",
    "boundary_layer_height",
    "mean_convective_precipitation_rate",
    "mean_total_precipitation_rate",
    "mean_surface_downward_long_wave_radiation_flux",
    "mean_surface_downward_short_wave_radiation_flux",
    "mean_top_downward_short_wave_radiation_flux",
    "mean_top_net_long_wave_radiation_flux",
    "mean_top_net_short_wave_radiation_flux",
    "mean_surface_latent_heat_flux",
    "mean_vertically_integrated_moisture_divergence",
    "total_column_water",
    "total_column_water_vapour",
    "total_column_rain_water",
    "total_column_cloud_liquid_water"
]

variables_3d = [
    "u_component_of_wind",
    "v_component_of_wind",
    "vertical_velocity",
    "temperature",
    "geopotential",
    "specific_humidity",
    "specific_cloud_liquid_water_content",
    "specific_rain_water_content",
    "fraction_of_cloud_cover",
]
area = [27, -67, 0, -37]  # lat_max, lon_min, lat_min, lon_max
levels = [str(lev) for lev in range(500, 700+1, 50)] +\
         [str(lev) for lev in range(750, 1000+1, 25)]

time_start = datetime.datetime(2020, 2, 2)
time_end = datetime.datetime(2020, 2, 3)
dt = datetime.timedelta(hours=1)


def main():
    time = time_start
    while time <= time_end:
        print(time)

        c.retrieve(
            "reanalysis-era5-single-levels",
            {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": variables_2d,
                "year": time.strftime("%Y"),
                "month": time.strftime("%m"),
                "day": time.strftime("%d"),
                "time": time.strftime("%H:%M"),
                "area": area,
            },
            datadir + "era5_{}_single_levels.nc".format(time.strftime("%Y%m%dT%H%M")),
        )

        c.retrieve(
            "reanalysis-era5-pressure-levels",
            {
                "product_type": "reanalysis",
                "format": "netcdf",
                "variable": variables_3d,
                "pressure_level": levels,
                "year": time.strftime("%Y"),
                "month": time.strftime("%m"),
                "day": time.strftime("%d"),
                "time": time.strftime("%H:%M"),
                "area": area,
            },
            datadir + "era5_{}_pressure_levels.nc".format(time.strftime("%Y%m%dT%H%M")),
        )

        time += dt


if __name__ == "__main__":
    main()
