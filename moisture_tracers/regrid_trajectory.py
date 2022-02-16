"""Extract a small grid of data from a trajectory within a large domain

Usage:
    regrid_trajectory.py from_coords
        <forecast_path> <forecast_start> <forecast_resolution>
        <trajectory_filename> <x0> <y0> <domain_size>
        [<output_path>]
    regrid_trajectory.py from_grid
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
from iris.cube import Cube

from irise.diagnostics.contours import haversine
from pylagranto import trajectory
from twinotter.util.scripting import parse_docopt_arguments

from moisture_tracers import grey_zone_forecast

# HALO: x0=302.283, y0=13.3
# Ron Brown: x0=305.5, y0=13.9


def main(
    forecast_path,
    forecast_start,
    forecast_resolution,
    trajectory_filename,
    from_coords=False,
    x0=None,
    y0=None,
    domain_size=None,
    from_grid=False,
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

    if from_grid:
        grid = iris.load_cube(initial_grid)
        grid_x = grid.coord("grid_longitude")
        grid_y = grid.coord("grid_latitude")
        x0 = grid_x.points.mean()
        y0 = grid_y.points.mean()

    for n, time in enumerate(tr.times):
        print(time)

        cubes = forecast.set_time(time)

        if n == 0 and from_coords:
            large_grid = cubes.extract_cube("atmosphere_boundary_layer_thickness")
            grid = create_grid(large_grid, x0, y0, domain_size)
            grid_x = grid.coord("grid_longitude")
            grid_y = grid.coord("grid_latitude")

        # Calculate the translation from the grid centre to the current trajectory
        # position
        # A trajectory ensemble of one trajectory so take the zeroth index
        dx = tr[time][0, 0] - x0
        dy = tr[time][0, 1] - y0

        # Create a new grid following the trajectory translation
        new_grid = translate_grid(grid_x, grid_y, dx, dy)

        # Regrid all cubes from the larger forecast grid to the translated small grid
        regridder = iris.analysis.AreaWeighted()
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
    xg = large_grid.coord("grid_longitude").points
    yg = large_grid.coord("grid_latitude").points

    xg, yg = np.meshgrid(xg, yg)

    mask = haversine([xg, yg], [x_centre, y_centre]) > resolution / 2

    xg = np.ma.masked_where(mask, xg)
    yg = np.ma.masked_where(mask, yg)

    cs = iris.Constraint(
        grid_longitude=lambda x: xg.min() <= x <= xg.max(),
        grid_latitude=lambda y: yg.min() <= y <= yg.max(),
    )

    return large_grid.extract(cs)


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    parse_docopt_arguments(main, __doc__)
