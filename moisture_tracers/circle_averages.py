"""
Create a netCDF with all variables averaged over a EUREC4A circle area

Usage:
    circle_averages.py <path> <start_time> <resolution> <grid> [<output_path>]
    circle_averages.py (-h | --help)

Arguments:
    <path>
    <start_time>
    <resolution>
    <grid>
    <output_path>

Options:
    -h --help
        Show this screen.
"""

import numpy as np
import iris
from iris.analysis import MEAN, RMS

from twinotter.external.eurec4a import lon, lat, r
from twinotter.util.scripting import parse_docopt_arguments

from . import grey_zone_forecast


def main(path, start_time, resolution, grid, output_path="./"):
    forecast = grey_zone_forecast(
        path, start_time=start_time, resolution=resolution, grid=grid
    )

    results = generate(forecast)

    iris.save(
        results,
        "{}/circle_averages_{}_{}_{}.nc".format(
            output_path,
            forecast.start_time.strftime("%Y%m%d"),
            resolution,
            grid,
        ),
    )


def generate(forecast):
    results = iris.cube.CubeList()

    for n, cubes in enumerate(forecast):
        print(forecast.lead_time)
        if n == 0:
            example_cube = cubes.extract_cube("air_pressure")
            glon = example_cube.coord("grid_longitude").points - 360
            glat = example_cube.coord("grid_latitude").points

            nz, ny, nx = example_cube.shape

            glon = np.broadcast_to(glon, [ny, nx])
            glat = np.broadcast_to(glat, [nx, ny]).transpose()

            in_circle = (np.sqrt((glon - lon) ** 2 + (glat - lat) ** 2) < r).astype(int)
            in_circle_3d = np.broadcast_to(in_circle, [nz, ny, nx])

            weights = {2: in_circle, 3: in_circle_3d}

        for cube in cubes:
            # Don't try to collapse coordinate cubes
            if cube.ndim in (2, 3):
                mean = cube.collapsed(
                    ["grid_latitude", "grid_longitude"],
                    MEAN,
                    weights=weights[cube.ndim],
                )

                std_dev = (cube - mean).collapsed(
                    ["grid_latitude", "grid_longitude"], RMS, weights=weights[cube.ndim]
                )
                mean.rename(cube.name() + "_mean")
                std_dev.rename(cube.name() + "_std_dev")
                results.append(mean)
                results.append(std_dev)

    return results.merge()


if __name__ == "__main__":
    parse_docopt_arguments(main, __doc__)
