"""Extract a small grid of data from a trajectory within a large domain

Usage:
    regrid_trajectory.py
        <forecast_path> <forecast_start> <forecast_resolution>
        <trajectory_filename> <initial_grid>
        [<output_path>]
    regrid_trajectory.py (-h | --help)

Arguments:
    <forecast_path>
    <forecast_start>
    <forecast_resolution>
    <trajectory_filename> The trajectoryEnsemble .pkl file produced by pylagranto
    <initial_grid> The grid to extract at the initial trajectory point. At further
        points along the trajectory the grid will be translated along the trajectory
    <output_path> Where to save the data

Options:
    -h --help
        Show this screen.
"""
import warnings

from dateutil.parser import parse as dateparse
import numpy as np
import iris
from iris.cube import Cube

from pylagranto import trajectory

from twinotter.util.scripting import parse_docopt_arguments

from moisture_tracers import grey_zone_forecast


def main(
    forecast_path,
    forecast_start,
    forecast_resolution,
    trajectory_filename,
    initial_grid,
    output_path=".",
):
    grid = iris.load_cube(initial_grid)
    grid_x = grid.coord("grid_longitude")
    grid_y = grid.coord("grid_latitude")

    tr = trajectory.load(trajectory_filename)

    start_time = dateparse(forecast_start)
    forecast = grey_zone_forecast(
        forecast_path,
        start_time=start_time,
        resolution=forecast_resolution,
        lead_times=range(1, 48 + 1),
        grid=None,
    )

    for time in tr.times:
        print(time)

        cubes = forecast.set_time(time)

        # Calculate the translation from the trajectory starting point to the current
        # trajectory position
        # A trajectory ensemble of one trajectory so take the zeroth index
        translation = tr[time][0] - tr[tr.times[0]][0]

        # Create a new grid following the trajectory translation
        new_grid = translate_grid(grid_x, grid_y, translation[0], translation[1])

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


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    parse_docopt_arguments(main, __doc__)
