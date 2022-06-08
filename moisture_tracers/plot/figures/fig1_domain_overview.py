"""Show the two domains used by overlaying a field from a hectometre scale simulation
on the same field from the 1.1km simulation providing the boundary conditions
"""
import warnings

import iris.plot as iplt
import matplotlib.pyplot as plt
import cmcrameri

import irise

from moisture_tracers import datadir, plotdir

variable = "total_column_water"
vmin, vmax = 20, 50


def main():
    cube_500m = irise.load(
        datadir + "D100m_500m/model-diagnostics_20200201T0000_T+35.nc"
    )
    cube_500m = cube_500m.extract_cube(variable)

    cube_1km = irise.load(
        datadir + "km1p1/model-diagnostics_20200201T0000_T+35.nc", variable
    )
    cube_1km = cube_1km.extract_cube(variable)

    plt.figure(figsize=(8, 6))

    for cube, cmap in [(cube_1km, "cmc.grayC"), (cube_500m, "cmc.oslo_r")]:
        iplt.pcolormesh(cube, vmin=vmin, vmax=vmax, cmap=cmap)

        if cmap == "cmc.grayC":
            cbar = plt.colorbar(extend="both", orientation="vertical")
            cbar.set_label("kg m$^{-2}$")

    # Plot the boundary of the hectometre-scale domain
    x = cube.coord("grid_longitude").points - 180
    y = cube.coord("grid_latitude").points
    plt.plot(
        [x[0], x[-1], x[-1], x[0], x[0]], [y[0], y[0], y[-1], y[-1], y[0]], color="r"
    )

    ax = plt.gca()
    ax.coastlines()
    ax.gridlines()
    plt.title("Total Column Water Feb 02 12:00\n500m and 1.1km T+36h")

    plt.savefig(plotdir + "fig1_domain_overview.png")


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()
