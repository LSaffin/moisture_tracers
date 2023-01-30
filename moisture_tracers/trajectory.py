"""

Usage:
    trajectory.py <path> <start_time> <resolution> <x0> <y0> <z0> <t0> [<output_path>]
    trajectory.py (-h | --help)

Arguments:
    <path>
    <start_time>
    <resolution>

Options:
    -h --help
        Show this screen.
"""

import warnings

import numpy as np

from twinotter.util.scripting import parse_docopt_arguments
from pylagranto import caltra
from pylagranto.datasets import MetUMStaggeredGrid

from moisture_tracers import grey_zone_forecast


# HALO: x0=302.283, y0=13.3
# Ron Brown (2nd Feb): x0=305.5, y0=13.9
# 24th Jan Case study:
#   x0=302.5, y0=11.75, t0=T+24h
#   x0=310.0, y0=15.0,  t0=T+48h

def main(path, start_time, resolution, x0, y0, z0, t0, output_path="./"):
    x0, y0, z0 = float(x0), float(y0), float(z0)
    t0 = int(t0)

    levels = ("height_above_reference_ellipsoid", [z0])

    forecast = grey_zone_forecast(
        path, start_time, resolution=resolution, grid=None, lead_times=range(1, 48 + 1)
    )
    trainp = np.array([[x0, y0, z0]])

    times = list(forecast._loader.files)
    datasource = MetUMStaggeredGrid(forecast._loader.files, levels=levels)

    if t0 == 1:
        traout = caltra.caltra(
            trainp, times, datasource, tracers=["x_wind", "y_wind"]
        )
    elif t0 == len(times):
        traout = caltra.caltra(
            trainp, times, datasource, fbflag=-1, tracers=["x_wind", "y_wind"]
        )
    else:
        traout_fwd = caltra.caltra(
            trainp, times[t0-1:], datasource, tracers=["x_wind", "y_wind"]
        )
        traout_bck = caltra.caltra(
            trainp, times[:t0], datasource, fbflag=-1, tracers=["x_wind", "y_wind"]
        )
        traout = traout_bck + traout_fwd

    traout.save(
        output_path + "{}_{}_{}E_{}N_{}m_T+{}.pkl".format(
            forecast.start_time.strftime("%Y%m%d"),
            resolution,
            format_float_for_file(x0),
            format_float_for_file(y0),
            format_float_for_file(z0),
            t0
        )
    )


def format_float_for_file(x):
    # Replace decimal point with a p (copying what was done for the UM files)
    return str(x).replace(".", "p")


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    parse_docopt_arguments(main, __doc__)
