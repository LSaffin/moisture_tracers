"""
Create a netCDF with all variables averaged over a EUREC4A circle area

Usage:
    domain_averages.py <path> <start_time> <resolution> <grid> [<output_path>]
    domain_averages.py (-h | --help)

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

import iris
from iris.analysis import MEAN, RMS
from iris.analysis.cartography import area_weights

from twinotter.util.scripting import parse_docopt_arguments

from . import grey_zone_forecast


def main(path, start_time, resolution, grid, output_path="./"):
    forecast = grey_zone_forecast(
        path,
        start_time=start_time,
        resolution=resolution,
        grid=grid,
    )

    results = generate(forecast)

    iris.save(
        results,
        "{}/domain_averages_{}_{}_{}.nc".format(
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
            weights = {2: area_weights(example_cube[0]), 3: area_weights(example_cube)}

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
