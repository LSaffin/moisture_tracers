import warnings

import numpy as np
import iris
from iris.coords import AuxCoord
from iris.analysis import MEAN, VARIANCE, PERCENTILE
import iris.plot as iplt
import matplotlib.pyplot as plt

from irise import convert
from myscripts import plotdir

from moisture_tracers import grey_zone_forecast, datadir
from moisture_tracers.anomaly_scale_decomposition import decompose_scales


resolutions = ["D100m_300m", "D100m_500m", "km1p1"]


def main():
    start_time = "2020-02-01"
    path = datadir + "regridded/"
    grid = "coarse_grid"

    # 4km grid coarse grained by a factor of 4 for 17.6km boxes at mesoscale
    coarse_factor = 4

    for resolution in resolutions:
        print(resolution)
        forecast = grey_zone_forecast(
            path,
            start_time=start_time,
            resolution=resolution,
            grid=grid,
            lead_times=range(1, 48 + 1),
        )

        # Cubelists to hold separate derived variables so that each on can be merged to
        # an individual cube with a time coordinate
        qt_var = iris.cube.CubeList()
        qt_var_meso = iris.cube.CubeList()
        qt_quartiles = iris.cube.CubeList()
        qt_quartiles_meso = iris.cube.CubeList()

        for lead_time in range(1, 48 + 1):
            print(lead_time)
            cubes = forecast.set_lead_time(hours=lead_time)

            # Total column water as a function of different scales
            qt = convert.calc("TOTAL COLUMN Q (WATER VAPOUR PATH)", cubes)
            qt_mean, qt_meso, qt_cu = decompose_scales(qt, coarse_factor=coarse_factor)

            # Variance of total column water at different scales
            qt_var.append(qt.collapsed(["grid_longitude", "grid_latitude"], VARIANCE))
            qt_var_meso.append(
                qt_meso.collapsed(["grid_longitude", "grid_latitude"], VARIANCE)
            )

            # Quartiles of total column water at different scales
            qt_quartiles.append(calc_quartiles(qt))
            qt_quartiles_meso.append(calc_quartiles(qt_meso + qt_mean))

        # Merge each result cubelist to a single cube with a time coordinate
        qt_var = qt_var.merge_cube()
        qt_var_meso = qt_var_meso.merge_cube()
        qt_quartiles = qt_quartiles.merge_cube()
        qt_quartiles_meso = qt_quartiles_meso.merge_cube()

        qt_var.rename("variance_of_total_water_content")
        qt_var_meso.rename("mesoscale_variance_of_total_water_content")
        qt_quartiles.rename("total_column_water")
        qt_quartiles_meso.rename("mesoscale_total_column_water")

        results = iris.cube.CubeList(
            [qt_var, qt_var_meso, qt_quartiles, qt_quartiles_meso]
        )
        iris.save(results, datadir + filename(resolution))


def filename(resolution):
    return "qt_diags_{}.nc".format(resolution)


def calc_quartiles(qt):
    quartiles = qt.collapsed(
        ["grid_longitude", "grid_latitude"], PERCENTILE, percent=[25, 50, 75]
    )

    qt_quartiles = iris.cube.CubeList()
    for n in range(4):
        if n == 0:
            mask = qt.data <= quartiles.data[0]
        elif n == 3:
            mask = qt.data > quartiles.data[2]
        else:
            mask = np.logical_and(
                quartiles.data[n - 1] < qt.data, qt.data <= quartiles.data[n]
            )

        qt_quartile = qt.collapsed(
            ["grid_longitude", "grid_latitude"], MEAN, weights=mask
        )
        qt_quartile.add_aux_coord(AuxCoord(points=n, long_name="quartile"))
        qt_quartiles.append(qt_quartile)
    qt_quartiles = qt_quartiles.merge_cube()

    return qt_quartiles


def make_plots():
    color = plt.cm.viridis(np.linspace(0, 1, 4))
    for resolution in resolutions:
        cubes = iris.load(datadir + filename(resolution))

        qt_var = cubes.extract_cube("variance_of_total_water_content")
        qt_var_meso = cubes.extract_cube("mesoscale_variance_of_total_water_content")
        qt_quartiles = cubes.extract_cube("total_column_water")
        qt_quartiles_meso = cubes.extract_cube("mesoscale_total_column_water")

        # Figure 1 - Fraction of variance of total column water at the mesoscale.
        # One plot for all resolutions
        plt.figure(1)
        iplt.plot(qt_var_meso / qt_var, label=resolution)

        # Figure 2 - Average total column water in each quartile.
        # One plot per resolution
        fig = plt.figure(2)
        for n in range(4):
            iplt.plot(qt_quartiles[:, n], label=n + 1, color=color[n])

        plt.legend()
        plt.ylabel("Total column water (kg m-2)")
        plt.title("Water content by quartiles: {}".format(resolution))
        plt.savefig(plotdir + "qt_diag_by_quartile_2nd_feb_{}.png".format(resolution))
        plt.close(fig)

        # Figure 3 - Difference in total column water between moistest and driest
        #            quartiles.
        # One plot for all resolutions
        plt.figure(3)
        iplt.plot(qt_quartiles[:, -1] - qt_quartiles[:, 0], label=resolution)

    fig = plt.figure(1)
    plt.legend()
    fig.autofmt_xdate()
    plt.title("Mesoscale variance / total variance of qt")
    plt.savefig(plotdir + "variance_ratio_2nd_feb.png")
    plt.close(fig)

    fig = plt.figure(3)
    plt.legend()
    fig.autofmt_xdate()
    plt.ylabel("Q4 - Q1 (kg m-2)")
    plt.title("Water content quartile difference")
    plt.savefig(plotdir + "qt_quartile_diffs_2nd_feb.png")
    plt.close(fig)


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()
    make_plots()
