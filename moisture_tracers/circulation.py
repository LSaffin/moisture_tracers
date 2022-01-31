"""

Usage:
    circulation.py <path> <start_time> <resolution> <grid> [<output_path>]
    circulation.py (-h | --help)

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
import pathlib

import parse
from dateutil.parser import parse as dateparse
import numpy as np
import matplotlib.pyplot as plt

from irise import convert
from irise.constants import omega
from twinotter.util.scripting import parse_docopt_arguments

from . import grey_zone_forecast


a = 6378100


def main(path, start_time, resolution, grid, output_path="./"):
    start_time = dateparse(start_time)
    forecast = grey_zone_forecast(
        path, start_time=start_time, resolution=resolution, grid=grid
    )
    circulation = get_circulations(forecast, plevs=np.arange(100000, 70000, -5000))

    np.save(
        "{}/circulation_{}_{}_{}.npy".format(
            output_path,
            start_time.strftime("%Y%m%d"),
            resolution,
            grid,
        ),
        np.array(circulation)
    )


def get_circulations(forecast, plevs):
    circulation = []
    for cubes in forecast:
        circ, circ_p = calc_circulation(cubes, levels=("air_pressure", plevs))
        circulation.append(circ)
    return circulation


def calc_circulation(cubes, levels):
    u = convert.calc("x_wind", cubes, levels=levels).data
    v = convert.calc("y_wind", cubes, levels=levels).data

    nz, ny, nx = u.shape

    p = convert.calc("air_pressure", cubes)
    lon = np.deg2rad(p.coord("grid_longitude").points)
    lat = np.deg2rad(p.coord("grid_latitude").points)

    dx_1 = np.broadcast_to(a * np.cos(lat[0]) * np.diff(lon), [nz, nx-1])
    dx_2 = np.broadcast_to(a * np.cos(lat[-1]) * np.diff(lon), [nz, nx-1])
    dy = np.broadcast_to(a * np.diff(lat), [nz, ny-1])

    # Calculate circulation anticlockwise along each boundary of the domain
    # bottom + right - top - left
    circ_u = np.sum((u[:, 0, :-1] + u[:, 0, 1:]) * 0.5 * dx_1, axis=1)
    circ_v = np.sum((v[:, :-1, -1] + v[:, 1:, -1]) * 0.5 * dy, axis=1)
    circ_u_2 = np.sum((u[:, -1, :-1] + u[:, -1, 1:]) * 0.5 * dx_2, axis=1)
    circ_v_2 = np.sum((v[:, :-1, 0] + v[:, 1:, 0]) * 0.5 * dy, axis=1)

    # Calculate the planetary circulation
    # This should be constant as we are using a fixed domain but it is a useful
    # comparison for strength of the relative circulation
    u_planetary = omega.data * a * np.cos([lat[0], lat[-1]])
    circ_p = np.sum((u_planetary[0]) * dx_1)
    circ_p_2 = np.sum((u_planetary[1]) * dx_2)

    return circ_u + circ_v - circ_u_2 - circ_v_2, circ_p - circ_p_2


def plot_all():
    path = pathlib.Path(".")
    filenames = path.glob("circulation_*.npy")

    for filename in filenames:
        print(filename)
        circulation = np.load(filename)
        resolution = parse.parse("circulation_{}.npy", str(filename))[0]
        plt.plot(circulation[:, 0], label=resolution)

    plt.legend()
    plt.show()


if __name__ == '__main__':
    parse_docopt_arguments(main, __doc__)
