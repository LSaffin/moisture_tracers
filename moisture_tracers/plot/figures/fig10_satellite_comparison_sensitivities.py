"""
A grid of satellite-like images from the UM forecasts
Each column in a different time and each row is a different resolution, with the
bottom row showing the satellite data on the same grid.
"""


import numpy as np
from iris.analysis import cartography
import iris.plot as iplt
import matplotlib.pyplot as plt

from moisture_tracers import (
    grey_zone_forecast,
    datadir,
    plotdir,
)
from moisture_tracers.plot.figures import labels, projection, lw_flux_plot_kwargs

satellite_path = datadir + "../../goes/2km_10min/"
varname = "toa_outgoing_longwave_flux"
cbar_label = "Model longwave flux (W m$^{-2}$)"

width_factor = 5


def main():
    resolutions = ["km1p1", "km2p2", "km4p4"]
    lead_times = [6, 12, 18, 24]
    fig = make_plot("20200202", "lagrangian_grid", resolutions, lead_times)
    fig.suptitle("Late start")
    fig.text(0.05, 0.95, "(a)", dict(fontsize="large"))
    plt.savefig(plotdir + "fig10_satellite_comparison_sensitivities_late_start.png")

    lead_times = [30, 36, 42, 48]
    fig = make_plot("20200201", "lagrangian_grid_no_evap", resolutions, lead_times)
    fig.suptitle("No Evap")
    fig.text(0.05, 0.95, "(b)", dict(fontsize="large"))
    plt.savefig(plotdir + "fig10_satellite_comparison_sensitivities_no_evap.png")


def make_plot(start_time, grid, resolutions, lead_times):
    nrows = len(resolutions)
    ncols = width_factor * len(lead_times) + 1

    fig = plt.figure(figsize=(8, nrows * 1.65))

    forecasts = dict()
    for resolution in resolutions:
        forecasts[resolution] = grey_zone_forecast(
            datadir + "regridded_vn12/",
            start_time=start_time,
            resolution=resolution,
            grid=grid,
            lead_times=lead_times,
        )

    for m, lead_time in enumerate(lead_times):
        col = width_factor * m
        for n, resolution in enumerate(resolutions):
            row = n
            plt.subplot2grid(
                (nrows, ncols),
                (row, col),
                colspan=width_factor,
                projection=projection,
            )

            cubes = forecasts[resolution].set_lead_time(hours=lead_time)
            cube = cubes.extract_cube(varname)

            print(resolution, cube.data.min(), cube.data.max())
            im1 = iplt.pcolormesh(cube, **lw_flux_plot_kwargs)

            # Put the time at the top of each column
            if n == 0:
                time = forecasts[resolution].current_time
                plt.title(time.strftime("%HZ"))

            # Put the resolution at the left side of each row
            if m == 0:
                # Need to re-grab the axis because iplt.pcolormesh creates a new
                # one
                ax = plt.gca()
                ax.get_yaxis().set_visible(True)
                ax.set_yticks([])
                ax.set_ylabel(labels[resolution])

    # Add colourbars
    # A vertical one for the model data spanning the model data rows
    ax = plt.subplot2grid((nrows, ncols), (0, ncols - 1), rowspan=nrows)
    cbar = plt.colorbar(im1, cax=ax, orientation="vertical", extend="both")
    cbar.set_label(cbar_label)

    return fig


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
