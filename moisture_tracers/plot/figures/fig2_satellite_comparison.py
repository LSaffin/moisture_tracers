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
    satellite_on_grid,
    datadir,
    plotdir,
)
from moisture_tracers.plot.figures import labels, projection

satellite_path = datadir + "../../goes/2km_10min/"
varname = "toa_outgoing_longwave_flux"
kwargs = dict(vmin=255, vmax=305, cmap="cividis_r")
cbar_label = "Model longwave flux (W m$^{-2}$)"

varname_sat = "temp_11_0um_nom"
kwargs_sat = dict(vmin=270, vmax=300, cmap="cmc.nuuk_r")
cbar_label_sat = r"Satellite 11 $\mu$m brightness temperature (K)"

height_factor = 5
width_factor = 5


def main():
    start_time = "20200201"
    grid = "coarse_grid"
    resolutions = ["D100m_300m", "D100m_500m", "km1p1", "km2p2", "km4p4"]
    lead_times = [30, 36, 42, 48]
    make_plot(start_time, grid, resolutions, lead_times)
    plt.savefig(
        plotdir + "fig2_satellite_comparison_{}_{}.png".format(start_time, grid)
    )


def make_plot(start_time, grid, resolutions, lead_times):
    nrows = height_factor * (len(resolutions) + 1) + 1
    ncols = width_factor * len(lead_times) + 1

    plt.figure(figsize=(8, nrows / 3))

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
            row = height_factor * n
            plt.subplot2grid(
                [nrows, ncols],
                [row, col],
                rowspan=height_factor,
                colspan=width_factor,
                projection=projection,
            )

            cubes = forecasts[resolution].set_lead_time(hours=lead_time)
            cube = cubes.extract_cube(varname)

            print(resolution, cube.data.min(), cube.data.max())
            im1 = iplt.pcolormesh(cube, **kwargs)

            # Put the time at the top of each column
            if n == 0:
                time = forecasts[resolution].current_time
                plt.title(time.strftime("%H:%M"))

            # Put the resolution at the left side of each row
            if m == 0:
                # Need to regrab the axis because iplt.pcolormesh creates a new
                # one
                ax = plt.gca()
                ax.get_yaxis().set_visible(True)
                ax.set_yticks([])
                ax.set_ylabel(labels[resolution])

        # GOES
        row = height_factor * len(resolutions)
        ax = plt.subplot2grid(
            [nrows, ncols],
            [row, col],
            rowspan=height_factor,
            colspan=width_factor,
            projection=projection,
        )

        # Interpolate satellite data to the model grid
        lons, lats = get_model_grid(cube)
        satellite_data = satellite_on_grid.goes_regridded(
            satellite_path,
            time,
            lons,
            lats,
            varname_sat,
        )
        satellite_data = cube.copy(data=satellite_data[varname_sat].values)
        print("satellite", satellite_data.data.min(), satellite_data.data.max())
        im2 = iplt.pcolormesh(satellite_data, **kwargs_sat)

        # Label the satellite in the leftmost plot
        if m == 0:
            ax.get_yaxis().set_visible(True)
            ax.set_yticks([])
            ax.set_ylabel("GOES")

    # Add colourbars
    # A vertical one for the model data spanning the model data rows
    ax = plt.subplot2grid(
        [nrows, ncols], [0, ncols - 1], rowspan=len(resolutions) * height_factor
    )
    cbar = plt.colorbar(im1, cax=ax, orientation="vertical")
    cbar.set_label(cbar_label)

    # A horizontal one for the satellite data at the bottom
    ax = plt.subplot2grid([nrows, ncols], [nrows - 1, 0], colspan=ncols - 1)
    cbar = plt.colorbar(im2, cax=ax, orientation="horizontal")
    cbar.set_label(cbar_label_sat)


def get_model_grid(cube):
    cs = cube.coord("grid_longitude").coord_system
    pole_lon = cs.grid_north_pole_longitude
    pole_lat = cs.grid_north_pole_latitude

    ny, nx = cube.shape

    rotated_lons = np.broadcast_to(cube.coord("grid_longitude").points, [ny, nx])
    rotated_lats = np.broadcast_to(
        cube.coord("grid_latitude").points, [nx, ny]
    ).transpose()

    lons, lats = cartography.unrotate_pole(
        rotated_lons, rotated_lats, pole_lon, pole_lat
    )

    return lons, lats


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
