"""Show the two domains used by overlaying a field from a hectometre scale simulation
on the same field from the 1.1km simulation providing the boundary conditions
"""
import warnings

import numpy as np
import iris.plot as iplt
import matplotlib.pyplot as plt
import cmcrameri

import irise
from twinotter.external import eurec4a

from moisture_tracers import datadir, plotdir
from moisture_tracers.plot.figures import z_levs

variable = "total_column_water"
vmin, vmax = 20, 50


def main():
    cube_500m = irise.load(
        datadir + "D100m_500m/model-diagnostics_20200201T0000_T+35.nc"
    )
    cube_500m = cube_500m.extract_cube(variable)

    cube_1km = irise.load(
        datadir + "km1p1/model-diagnostics_20200201T0000_T+35.nc",
    )
    cube_1km = cube_1km.extract_cube(variable)

    fig, ax_dict = plt.subplot_mosaic(
        """
        aaaaaaaaaaaa
        aaaaaaaaaaaa
        aaaaaaaaaaaa
        .bbbbbbbbb..
        """,
        figsize=(8, 8),
    )

    plt.axes(ax_dict["a"])
    for cube, cmap in [(cube_1km, "cmc.grayC"), (cube_500m, "cmc.oslo_r")]:
        iplt.pcolormesh(cube, vmin=vmin, vmax=vmax, cmap=cmap)

        if cmap == "cmc.grayC":
            cbar = plt.colorbar(extend="both", orientation="vertical")
            cbar.set_label("kg m$^{-2}$")

    # Plot the boundary of the hectometre-scale domain
    x = cube.coord("grid_longitude").points - 180
    y = cube.coord("grid_latitude").points
    plt.plot(
        [x[0], x[-1], x[-1], x[0], x[0]], [y[0], y[0], y[-1], y[-1], y[0]], color="k", lw=2,
    )

    ax = plt.gca()
    eurec4a.add_halo_circle(ax, alpha=0.75, lw=1)
    ax.coastlines()
    gl = ax.gridlines()
    gl.ylabels_left = True
    for xc in range(40, 70, 5):
        plt.text(180 - xc, -0.5, r"{}$\degree$W".format(xc), ha="center", va="top")

    ax.text(0.0, 1.05, "(a)", dict(fontsize="large"), transform=ax.transAxes)
    plt.title(
        "Total Column Water (500m and 1.1km)\n" r"12Z 2$^\mathrm{nd}$ Feb (T+36h)"
    )

    z_rho = (z_levs[1:] + z_levs[:-1]) / 2
    dz = z_rho[1:] - z_rho[:-1]
    ax_dict["b"].plot(dz*1e3, z_levs[1:-1], "-kx")
    ax_dict["b"].set_xlim(0, 250)
    ax_dict["b"].set_ylim(0, 5)
    ax_dict["b"].set_xlabel("Vertical grid spacing (m)")
    ax_dict["b"].set_ylabel("Height (km)")
    ax_dict["b"].grid(which="both")
    ax_dict["b"].text(0.01, 0.9, "(b)", dict(fontsize="large"), transform=ax_dict["b"].transAxes)

    plt.savefig(plotdir + "fig1_domain_overview.png")


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()
