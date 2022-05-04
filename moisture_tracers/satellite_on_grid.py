"""Plot satellite data regridded to a forecast grid

Usage:
    satellite_on_grid.py
        <satellite_path> <forecast_filename>
        <first_time> <last_time> <interval>
        <plot_type>
        [<output_path>]
    satellite_on_grid.py (-h | --help)

Arguments:
    <satellite_path>
    <forecast_filename> A file containing variables on a grid to match the satellite
        data to
    <first_time>
    <last_time>
    <interval> Time interval in minutes between each plot of the satellite data
    <output_path>
    <plot_type> temperature or geocolor

Options:
    -h --help
        Show this screen.
"""


import datetime

from dateutil.parser import parse
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import cartopy.crs as ccrs
import xarray as xr
import iris
from iris.analysis import cartography
from iris.util import squeeze

from twinotter.util.scripting import parse_docopt_arguments
from twinotter.external.eurec4a import add_halo_circle
from twinotter.external.goes import load_nc, load_ceres
from twinotter.external.goes.plot import geocolor


def main(
    satellite_path,
    forecast_filename,
    first_time,
    last_time,
    interval,
    plot_type,
    output_path=".",
):
    t0 = parse(first_time)
    t1 = parse(last_time)
    dt = datetime.timedelta(minutes=int(interval))

    lons, lats = get_grid(forecast_filename)
    projection = ccrs.PlateCarree()

    time = t0
    while time <= t1:
        print(time)
        goes_data_grid = goes_regridded(
            satellite_path, time, lons, lats, plot_types[plot_type]["bands"]
        )

        ax = plt.axes(projection=projection)
        im = plot_types[plot_type]["plot_func"](ax, goes_data_grid, projection)
        add_halo_circle(ax)

        if plot_type != "geocolor":
            plt.colorbar(im, orientation="horizontal")
        plt.savefig(
            output_path
            + "/{}_regrid_T+{:02d}.png".format(
                plot_type, int((time - t0).total_seconds() // 3600)
            )
        )
        plt.close()

        time += dt


def toa_brightness_temperature(ax, ds, projection):
    x = ds.longitude
    y = ds.latitude
    return ax.pcolormesh(
        x,
        y,
        ds["temp_11_0um_nom"],
        transform=projection,
        vmin=280,
        vmax=300,
        cmap="cividis_r",
    )


def goes_regridded(path, time, lons, lats, variables, source="goes"):
    if source.lower() == "goes":
        ds = load_nc(path, time)
    elif source.lower() == "ceres":
        ds = load_ceres(path, time)
    else:
        raise KeyError("Source {} not supported. Select either 'goes' or 'ceres'".format(source))

    # Flatten and remove NaNs. The NaNs aren't in a square grid so can't be dropped on
    # loading
    mask = np.isnan(ds.longitude.values.flatten())
    x = ds.longitude.values.flatten()[~mask]
    y = ds.latitude.values.flatten()[~mask]

    # Make sure to loop over variables as a list if only one is requested
    if isinstance(variables, str):
        variables = [variables]

    # Interpolate the satellite data to a regular grid
    goes_data_grid = xr.Dataset(coords=dict(longitude=lons[0, :], latitude=lats[:, 0]))
    for variable in variables:
        data = ds[variable].values.flatten()[~mask]
        variable_on_grid = griddata((x, y), data, (lons, lats))

        goes_data_grid[variable] = (["latitude", "longitude"], variable_on_grid)

    return goes_data_grid


def get_grid(forecast_filename):
    """Extract the longitude/latitude grid from a netCDF file containing
    surface_pressure and grid data


    Args:
        forecast_filename:

    Returns:
        tuple: 2x 2d np.array. Longitude and latitude on the model grid
    """
    grid = squeeze(iris.load_cube(forecast_filename, "surface_air_pressure"))

    cs = grid.coord("grid_longitude").coord_system
    pole_lon = cs.grid_north_pole_longitude
    pole_lat = cs.grid_north_pole_latitude

    ny, nx = grid.shape

    rotated_lons = np.broadcast_to(grid.coord("grid_longitude").points, [ny, nx])
    rotated_lats = np.broadcast_to(
        grid.coord("grid_latitude").points, [nx, ny]
    ).transpose()

    lons, lats = cartography.unrotate_pole(
        rotated_lons, rotated_lats, pole_lon, pole_lat
    )

    return lons, lats


plot_types = dict(
    temperature=dict(
        bands=["temp_11_0um_nom"],
        plot_func=toa_brightness_temperature,
    ),
    geocolor=dict(
        bands=["refl_0_65um_nom", "refl_0_86um_nom", "refl_0_47um_nom"],
        plot_func=geocolor,
    ),
)


if __name__ == "__main__":
    parse_docopt_arguments(main, __doc__)
