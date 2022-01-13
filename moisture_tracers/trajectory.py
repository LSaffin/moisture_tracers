"""

Usage:
    trajectory.py <path> <start_time> <resolution> <grid>
    trajectory.py (-h | --help)

Arguments:
    <path>
    <start_time>
    <resolution>
    <grid>

Options:
    -h --help
        Show this screen.
"""

import warnings

from dateutil.parser import parse as dateparse
import numpy as np

from twinotter.util.scripting import parse_docopt_arguments
from pylagranto import caltra
from pylagranto.datasets import MetUMStaggeredGrid

from moisture_tracers import grey_zone_forecast


def main(path, start_time, resolution, grid):
    start_time = dateparse(start_time)

    x0 = 302.5
    y0 = 13.5
    z0 = 500
    levels = ("height_above_reference_ellipsoid", [z0])

    forecast = grey_zone_forecast(
        path, start_time, resolution=resolution, grid=grid, lead_times=range(1, 48 + 1)
    )
    trainp = np.array([[x0, y0, z0]])

    times = list(forecast._loader.files)
    datasource = MetUMStaggeredGrid(forecast._loader.files, levels=levels)

    traout = caltra.caltra(
        trainp, times, datasource, fbflag=-1, tracers=["x_wind", "y_wind"]
    )

    traout.save(
        "trajectories_{}_{}_{}m.pkl".format(
            start_time.strftime("%Y%m%d"), resolution, z0
        )
    )


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    parse_docopt_arguments(main, __doc__)
