"""
Usage:
    aggregation.py
        <path> <start_time> <resolution> <model_grid>
        [--output_path=<path>]
    aggregation_terms.py (-h | --help)

Arguments:
    <path>
    <start_time>
    <resolution>
    <model_grid>
    <output_path>

Options:
    -h --help
        Show this screen.
"""


from dateutil.parser import parse as dateparse
import iris
from iris.analysis import SUM
import iris.plot as iplt
import matplotlib.pyplot as plt

from irise import grid

from twinotter.util.scripting import parse_docopt_arguments
from moisture_tracers.aggregation_terms import long_names


def main(path, start_time, resolution, model_grid, output_path="./"):
    """
    Calculate the quartiles of column moisture at each lead time
    """
    start_time = dateparse(start_time)

    cubes = iris.load(
        path
        + "aggregation_terms_by_quartile_{}_{}_{}.nc".format(
            start_time.strftime("%Y%m%d"),
            resolution,
            model_grid,
        )
    )

    times = grid.get_datetime(cubes[0])
    for time in times:
        cubes_at_time = cubes.extract(
            iris.Constraint(time=lambda cell: cell.point == time)
        )
        vertical_profile(cubes_at_time)
        plt.savefig(
            output_path
            + "aggregation_terms/aggregation_terms_{}_{}_{}_T+{}".format(
                start_time.strftime("%Y%m%d"),
                resolution,
                model_grid,
                (time - start_time).total_seconds() // 3600,
            )
        )
        plt.close()

    column_average(cubes)
    plt.savefig(
        output_path
        + "aggregation_terms/aggregation_terms_column_sum_{}_{}_{}".format(
            start_time.strftime("%Y%m%d"),
            resolution,
            model_grid,
        )
    )
    plt.close()

    column_water_variation(cubes)
    plt.savefig(
        output_path
        + "column_water_aggregation/column_water_aggregation_{}_{}_{}".format(
            start_time.strftime("%Y%m%d"),
            resolution,
            model_grid,
        )
    )
    plt.close()

    column_water_by_quartile(cubes)
    plt.savefig(
        output_path
        + "column_water_aggregation/column_water_by_quartile_{}_{}_{}".format(
            start_time.strftime("%Y%m%d"),
            resolution,
            model_grid,
        )
    )
    plt.close()


def vertical_profile(cubes):
    # Aggregation terms
    fig, axes = plt.subplots(2, 2, sharex="all", sharey="all", figsize=(12, 8))

    z = None
    for n, short_name in enumerate(["a", "b_v", "b_h", "c"]):
        plt.axes(axes[n // 2, n % 2])
        plt.title(long_names[short_name])
        plt.axvline(color="k")
        cube = cubes.extract_cube(long_names[short_name])
        if z is None:
            z = cube.coord("height_above_reference_ellipsoid")

        for m in range(4):
            iplt.plot(cube[m, :], z, label=m + 1)

    plt.legend()


def column_average(cubes):
    dz = None
    for n, short_name in enumerate(["a", "b_v", "b_h", "c"]):
        cube = cubes.extract_cube(long_names[short_name])
        if dz is None:
            dz = grid.thickness(cube)

        cube_col = cube.collapsed(
            ["atmosphere_hybrid_height_coordinate"], SUM, weights=dz.data
        )

        iplt.plot(cube_col[:, -1], label=short_name)

    plt.gcf().autofmt_xdate()
    plt.legend()


def column_water_variation(cubes):
    # Total aggregation
    qt_by_quartile = cubes.extract_cube("total_column_water")
    iplt.plot(qt_by_quartile[:, -1] - qt_by_quartile[:, 0])
    plt.ylabel("total column water difference")
    plt.gcf().autofmt_xdate()


def column_water_by_quartile(cubes):
    qt_by_quartile = cubes.extract_cube("total_column_water")
    for n in range(4):
        iplt.plot(qt_by_quartile[:, n], label=n + 1)

    plt.ylabel("total column water")
    plt.gcf().autofmt_xdate()
    plt.legend()


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    parse_docopt_arguments(__doc__, main)
