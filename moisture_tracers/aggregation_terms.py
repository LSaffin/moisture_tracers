"""
Calculation of the terms in the tendency of mesoscale aggregation from
Narenpitak at al. (2021). The terms are derived from the equations of
Bretherton and Blossey (2017)

Usage:
    aggregation_terms.py
        <path> <start_time> <resolution> <data_grid>
        [<coarse_factor>]
        [--output_path=<path>]
    aggregation_terms.py (-h | --help)

Arguments:
    <path>
    <start_time>
    <resolution>
    <data_grid>
    <coarse_factor>

Options:
    -h --help
        Show this screen.
"""

import numpy as np
import iris
from iris.analysis import AreaWeighted, MEAN, SUM, PERCENTILE, Linear
from iris.analysis.calculus import differentiate
from iris.coords import AuxCoord
from iris.util import broadcast_to_shape
import iris.plot as iplt
import matplotlib.pyplot as plt

from irise import calculus, convert, grid

from twinotter.util.scripting import parse_docopt_arguments
from pylagranto import trajectory

from moisture_tracers import datadir, grey_zone_forecast
from moisture_tracers.quicklook import specific_fixes
from moisture_tracers.anomaly_scale_decomposition import decompose_scales


long_names = dict(
    a="advection_of_mesoscale_variability",
    b_v="vertical_cumulus_fluxes",
    b_h="horizontal_cumulus_fluxes",
    c="mesoscale_vertical_advection_of_background_moisture",
)


def main(path, start_time, resolution, data_grid, coarse_factor=4, output_path="."):
    """
    Calculate the aggregation terms in each quartile of column moisture at each lead
    time in a forecast and save to a netCDF file
    """
    coarse_factor = int(coarse_factor)

    forecast = grey_zone_forecast(
        path=path, start_time=start_time, resolution=resolution, grid=data_grid
    )

    if data_grid == "lagrangian_grid":
        tr = trajectory.load(
            datadir + "trajectories/trajectories_{}_{}_500m.pkl".format(
                forecast.start_time.strftime("%Y%m%d"),
                resolution,
            )
        )[0]

    vars_by_quartile = iris.cube.CubeList()
    for lead_time in range(24, 48 + 1):
        print(lead_time)

        cubes = forecast.set_lead_time(hours=lead_time)
        specific_fixes(cubes)

        if data_grid == "lagrangian_grid":
            subtract_winds(cubes, tr)

        qt_meso, A, B_v, B_h, C = get_aggregation_terms(cubes, coarse_factor)

        qt_column = convert.calc("total_column_water", cubes)
        qt_column = qt_column.regrid(qt_meso, AreaWeighted())
        for cube in average_by_quartile(qt_column, [A, B_v, B_h, C, qt_column]):
            cube.remove_coord("grid_longitude")
            cube.remove_coord("grid_latitude")
            vars_by_quartile.append(cube)

    vars_by_quartile = vars_by_quartile.merge()
    iris.save(
        vars_by_quartile,
        "{}/aggregation_terms_by_quartile_{}_{}_{}.nc".format(
            output_path,
            forecast.start_time.strftime("%Y%m%d"),
            resolution,
            data_grid,
        ),
    )


def subtract_winds(cubes, tr):
    u = cubes.extract_cube("x_wind")
    v = cubes.extract_cube("y_wind")

    time = grid.get_datetime(u)
    t_index = tr.times.index(time)

    u.data -= tr["x_wind"][t_index]
    v.data -= tr["y_wind"][t_index] 


def get_aggregation_terms(cubes, coarse_factor):
    """
    Calculate the aggregation terms from the cubes. The coarse factor is the ratio
    between the gridbox size in the cubes and the gridbox size used for mesoscale
    anomalies.

    Args:
        cubes (iris.cube.CubeList):
        coarse_factor (int):

    Returns:
        tuple:
    """

    qt = convert.calc("specific_total_water_content", cubes)
    u = cubes.extract_cube("x_wind")
    v = cubes.extract_cube("y_wind")
    w = cubes.extract_cube("upward_air_velocity")
    density = cubes.extract_cube("air_density")

    qt_mean, qt_meso, qt_cu = decompose_scales(qt, coarse_factor=coarse_factor)
    u_mean, u_meso, u_cu = decompose_scales(u, coarse_factor=coarse_factor)
    v_mean, v_meso, v_cu = decompose_scales(v, coarse_factor=coarse_factor)
    w_mean, w_meso, w_cu = decompose_scales(w, coarse_factor=coarse_factor)

    A = advection_of_mesoscale_variability(qt_meso, u_meso + u_mean, v_meso + v_mean)
    B_v, B_h = cumulus_fluxes(density, qt_meso, qt_cu, u_cu, v_cu, w_cu)
    C = mesoscale_vertical_advection_of_mean_state(qt_mean, w_meso)

    return qt_meso, A, B_v, B_h, C


def average_by_quartile(qt_column, cubes):
    """
    Get the average of each of the cubes in the four quartiles of qt_column

    Args:
        qt_column (iris.cube.Cube):
        cubes (iris.cube.CubeList):

    Returns:
        iris.cube.CubeList:
    """

    quartiles = qt_column.collapsed(
        ["grid_longitude", "grid_latitude"], PERCENTILE, percent=[25, 50, 75]
    )

    vars_by_quartile = iris.cube.CubeList()
    for n in range(4):
        if n == 0:
            mask = qt_column.data <= quartiles.data[0]
        elif n == 3:
            mask = qt_column.data > quartiles.data[2]
        else:
            mask = np.logical_and(
                quartiles.data[n - 1] < qt_column.data,
                qt_column.data <= quartiles.data[n],
            )
        mask = broadcast_to_shape(mask, cubes[0].shape, [1, 2])

        for m, cube in enumerate(cubes):
            if cube.ndim == 2:
                by_quartile = cube.collapsed(
                    ["grid_longitude", "grid_latitude"], MEAN, weights=mask[0]
                )
            else:
                by_quartile = cube.collapsed(
                    ["grid_longitude", "grid_latitude"], MEAN, weights=mask
                )
            by_quartile.add_aux_coord(AuxCoord(points=n + 1, long_name="quartile"))
            vars_by_quartile.append(by_quartile)

    return vars_by_quartile.merge()


def plot_quartiles(vars_by_quartile):
    fig, axes = plt.subplots(
        nrows=(len(vars_by_quartile) + 1) // 2, ncols=2, sharex="all", sharey="all"
    )

    z = vars_by_quartile[0].coord("altitude")
    color = plt.cm.viridis(np.linspace(0, 1, 4))
    for m, var in enumerate(vars_by_quartile):
        plt.axes(axes[m % 2, m // 2])
        for n in range(4):
            iplt.plot(var[n], z, label=n + 1, color=color[n])
        plt.title(var.name())

    plt.axes(axes[0, 0])
    plt.legend()
    plt.show()


def plot_timeseries():
    cubes = iris.load("aggregation_terms_by_quartile_t+*.nc")

    dz = grid.thickness(cubes[0])

    for cube in cubes:
        column_mean = cube.collapsed(
            ["atmosphere_hybrid_height_coordinate"], SUM, weights=dz.data
        )
        iplt.plot(column_mean[:, -1], label=cube.name())

    plt.legend()
    plt.gcf().autofmt_xdate()
    plt.show()


def advection_of_mesoscale_variability(qt_meso, u_meso, v_meso):
    dqt_dx, dqt_dy, _ = calculus.grad(qt_meso)

    A = -(u_meso * dqt_dx + v_meso * dqt_dy)
    A.rename("advection_of_mesoscale_variability")

    return A


def cumulus_fluxes(density, qt_meso, qt_cu, u_cu, v_cu, w_cu):
    wq = density * w_cu * qt_cu
    wq = wq.regrid(qt_meso, AreaWeighted())

    z = qt_meso.coord("altitude")
    dwq_dz = differentiate(wq, "altitude")
    dwq_dz = dwq_dz.interpolate([(z.name(), z.points)], Linear())

    density_meso = density.regrid(qt_meso, AreaWeighted())

    units = dwq_dz.units
    dwq_dz = density_meso.copy(data=dwq_dz.data)
    dwq_dz.units = units

    B_v = dwq_dz / density_meso

    B_v.rename("vertical_cumulus_fluxes")

    uq = (u_cu * qt_cu).regrid(qt_meso, AreaWeighted())
    vq = (v_cu * qt_cu).regrid(qt_meso, AreaWeighted())

    duq_dx = calculus.polar_horizontal(uq, "x")
    duq_dx = duq_dx.regrid(qt_meso, AreaWeighted())

    dvq_dy = calculus.polar_horizontal(vq, "y")
    dvq_dy = dvq_dy.regrid(qt_meso, AreaWeighted())

    B_h = -(duq_dx + dvq_dy)

    B_h.rename("horizontal_cumulus_fluxes")

    return B_v, B_h


def mesoscale_vertical_advection_of_mean_state(qt_mean, w_meso):
    dqt_dz = differentiate(qt_mean, "altitude")

    z = w_meso.coord("altitude")
    dqt_dz = dqt_dz.interpolate([(z.name(), z.points)], Linear())
    dqt_dz.replace_coord(w_meso.coord("atmosphere_hybrid_height_coordinate"))
    dqt_dz = grid.broadcast_to_cube(dqt_dz, w_meso)

    C = -w_meso * dqt_dz
    C.rename("mesoscale_vertical_advection_of_background_moisture")

    return C


def precipitation_mass_flux():
    pass


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")

    parse_docopt_arguments(main, __doc__)
    #plot_timeseries()
