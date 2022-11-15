"""
Plot satellite data regridded to a forecast grid for each time in the forecast output

Usage:
    satellite_on_lagrangian_grid.py
        <path> <start_time> <resolution> <grid>
        <satellite_path> <plot_type>
        [<output_path>]
    satellite_on_lagrangian_grid.py (-h | --help)

Arguments:
    <path>
        The path to the forecast data
    <start_time>
        Start time of the forecast
    <resolution>
        Resolution of the forecast
    <grid>
        The grid the forecast data is on (lagrangian_grid)
    <satellite_path>
        The path to the satellite data
    <plot_type>
        How to plot the satellite data. Either "geocolor" or "temperature"
    <output_path>
        Where to save the figures

Options:
    -h --help
        Show this screen.
"""

import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from twinotter.util.scripting import parse_docopt_arguments
from twinotter.external.eurec4a import add_halo_circle

from moisture_tracers import grey_zone_forecast
from moisture_tracers.satellite_on_grid import get_grid, goes_regridded, plot_types


def main(
    satellite_path,
    path,
    start_time,
    resolution,
    grid,
    plot_type,
    output_path=".",
):
    forecast = grey_zone_forecast(
        path,
        start_time=start_time,
        resolution=resolution,
        grid=grid,
    )

    projection = ccrs.PlateCarree()
    for cubes in forecast:
        time = forecast.current_time
        print(time)
        cube, lons, lats = get_grid(cubes)

        try:
            goes_data_grid = goes_regridded(
                satellite_path, time, lons, lats, plot_types[plot_type]["bands"]
            )

            ax = plt.axes(projection=projection)
            im = plot_types[plot_type]["plot_func"](ax, goes_data_grid, projection)
            ax.coastlines()
            add_halo_circle(ax)

            if plot_type != "geocolor":
                plt.colorbar(im, orientation="horizontal")
            plt.savefig(
                output_path
                + "/{}_regrid_lagrangian_{}.png".format(
                    plot_type, time.strftime("%Y%m%d_%H%M")
                )
            )
            plt.close()
        except FileNotFoundError as e:
            print(e)


if __name__ == "__main__":
    parse_docopt_arguments(main, __doc__)
