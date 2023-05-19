"""Extract a small grid of data from a trajectory within a large domain

Usage:
    regrid_trajectory.py to_size
        <forecast_path> <forecast_start> <forecast_resolution>
        <trajectory_filename> <domain_size>
        [<output_path>]
    regrid_trajectory.py to_grid
        <forecast_path> <forecast_start> <forecast_resolution>
        <trajectory_filename> <initial_grid>
        [<output_path>]
    regrid_trajectory.py (-h | --help)

Arguments:
    <forecast_path>
    <forecast_start>
    <forecast_resolution>
    <trajectory_filename> The trajectoryEnsemble .pkl file produced by pylagranto
    <output_path> Where to save the data

Options:
    -h --help
        Show this screen.
"""
import warnings

import numpy as np
import iris
from iris.analysis import AreaWeighted
from iris.cube import Cube

from irise.diagnostics.contours import haversine
from pylagranto import trajectory
from twinotter.util.scripting import parse_docopt_arguments

from moisture_tracers import grey_zone_forecast


def main(
    forecast_path,
    forecast_start,
    forecast_resolution,
    trajectory_filename,
    to_size=False,
    domain_size=None,
    to_grid=False,
    initial_grid=None,
    output_path=".",
):
    tr = trajectory.load(trajectory_filename)

    forecast = grey_zone_forecast(
        forecast_path,
        start_time=forecast_start,
        resolution=forecast_resolution,
        lead_times=range(1, 48 + 1),
        grid=None,
    )

    if to_grid:
        grid = iris.load_cube(initial_grid)
        grid_x = grid.coord(axis="x", dim_coords=True)
        grid_y = grid.coord(axis="y", dim_coords=True)
        x0 = grid_x.points.mean()
        y0 = grid_y.points.mean()

    for n, cubes in enumerate(forecast):
        time = forecast.current_time
        print(time)

        if n == 0 and to_size:
            large_grid = cubes.extract_cube("atmosphere_boundary_layer_thickness")
            x0 = tr[time][0, 0]
            y0 = tr[time][0, 1]
            grid = create_grid(large_grid, x0, y0, float(domain_size))
            grid_x = grid.coord(axis="x", dim_coords=True)
            grid_y = grid.coord(axis="y", dim_coords=True)

        # Calculate the translation from the grid centre to the current trajectory
        # position
        # A trajectory ensemble of one trajectory so take the zeroth index
        dx = tr[time][0, 0] - x0
        dy = tr[time][0, 1] - y0

        # Create a new grid following the trajectory translation
        new_grid = translate_grid(grid_x, grid_y, dx, dy)

        # Regrid all cubes from the larger forecast grid to the translated small grid
        regridder = AreaWeighted()
        newcubes = iris.cube.CubeList()
        for cube in cubes:
            if cube.ndim > 1 and cube.name() not in ["longitude", "latitude"]:
                newcube = cube.regrid(new_grid, regridder)
                newcubes.append(newcube)

        iris.save(
            newcubes,
            "{}/{}_{}_T+{:02d}_lagrangian_grid.nc".format(
                output_path,
                forecast.start_time.strftime("%Y%m%dT%H%M"),
                forecast_resolution,
                int(forecast.lead_time.total_seconds() // 3600),
            ),
        )


def translate_grid(x, y, offset_x, offset_y):
    new_x_coord = x.copy(points=x.points + offset_x, bounds=x.bounds + offset_x)
    new_y_coord = y.copy(points=y.points + offset_y, bounds=y.bounds + offset_y)

    return Cube(
        data=np.zeros([len(y.points), len(x.points)]),
        dim_coords_and_dims=[(new_y_coord, 0), (new_x_coord, 1)],
    )


def create_grid(large_grid, x_centre, y_centre, resolution):
    lon = large_grid.coord(axis="x", dim_coords=True)
    lat = large_grid.coord(axis="y", dim_coords=True)

    # Find all longitude and latitude points within a circle of diameter=resolution
    # centred on (x_centre, y_centre)
    xg, yg = np.meshgrid(lon.points, lat.points)
    mask = haversine([xg, yg], [x_centre, y_centre]) > resolution / 2
    xg = np.ma.masked_where(mask, xg)
    yg = np.ma.masked_where(mask, yg)

    # Extract a square grid where the outermost points are defined by the circle edges
    # The box bounds the circle
    cube = large_grid.intersection(
        **{
            lon.name(): (xg.min(), xg.max()),
            lat.name(): (yg.min(), yg.max()),
        },
        ignore_bounds=True,
    )

    return cube


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    parse_docopt_arguments(main, __doc__)
