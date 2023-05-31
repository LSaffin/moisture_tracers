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
import datetime
import warnings

import numpy as np

from twinotter.util.scripting import parse_docopt_arguments
from pylagranto import caltra
from pylagranto.datasets import MetUMStaggeredGrid

from moisture_tracers import grey_zone_forecast


trajectory_filename = "{start_time}_{resolution}_{x0}E_{y0}N_{z0}{units}_" \
                      "T+{lead_time:02d}.pkl"

# Inner-domain centre: x0=302.5, y0=13.5, t0=48
# HALO: x0=302.283, y0=13.3
# Ron Brown (2nd Feb): x0=305.5, y0=13.9
# 24th Jan Case study:
#   x0=302.5, y0=11.75, t0=T+24h
#   x0=310.0, y0=15.0,  t0=T+48h


def _command_line_interface(path, start_time, resolution, x0, y0, z0, t0, output_path="./"):
    forecast = grey_zone_forecast(
        path, start_time, resolution=resolution, grid=None, lead_times=range(1, 48 + 1)
    )

    traout = calculate_trajectory(
        forecast, float(x0), float(y0), float(z0), int(t0), "height_above_reference_ellipsoid"
    )

    traout.save(
        output_path + trajectory_filename.format(
            start_time=forecast.start_time.strftime("%Y%m%d"),
            resolution=resolution,
            x0=format_float_for_file(x0),
            y0=format_float_for_file(y0),
            z0=format_float_for_file(z0),
            t0=t0,
            units="m",
        )
    )


def calculate_trajectory(forecast, x0, y0, z0, t0, zcoord):
    levels = (zcoord, [z0])
    trainp = np.array([[x0, y0, z0]])

    times = list(forecast._loader.files)
    datasource = MetUMStaggeredGrid(forecast._loader.files, levels=levels)

    time_traj = forecast.start_time + datetime.timedelta(hours=t0)
    if time_traj == times[0]:
        traout = caltra.caltra(
            trainp, times, datasource, tracers=["x_wind", "y_wind"]
        )
    elif time_traj == times[-1]:
        traout = caltra.caltra(
            trainp, times, datasource, fbflag=-1, tracers=["x_wind", "y_wind"]
        )
    else:
        times_fwd = [time for time in times if time <= time_traj]
        traout_fwd = caltra.caltra(
            trainp, times_fwd, datasource, tracers=["x_wind", "y_wind"]
        )

        times_bck = [time for time in times if time >= time_traj]
        traout_bck = caltra.caltra(
            trainp, times_bck, datasource, fbflag=-1, tracers=["x_wind", "y_wind"]
        )
        traout = traout_bck + traout_fwd

    return traout


def format_float_for_file(x):
    # Replace decimal point with a p (copying what was done for the UM files)
    return str(x).replace(".", "p")


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    parse_docopt_arguments(_command_line_interface, __doc__)
