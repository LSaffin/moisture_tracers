import datetime

import iris
import iris.plot as iplt
import numpy as np
import matplotlib.pyplot as plt

from moisture_tracers import datadir, plotdir
from moisture_tracers.plot.figures import linestyles, alphas, labels, date_format

aggregation_terms_fname = "diagnostics_vn12/aggregation_terms_by_quartile_{}_{}_{}.nc"
resolutions = dict(
    coarse_grid=["km1p1", "km2p2", "km4p4"],
    lagrangian_grid=["km1p1", "km2p2", "km4p4"],
    lagrangian_grid_no_evap=["km1p1", "km2p2", "km4p4"],
    lagrangian_grid_Ron_Brown=["km1p1", "km2p2", "km4p4"],
)

variable = "total_column_water"


def main():
    fig, axes = plt.subplots(2, 1, sharex="all", figsize=(8, 8))

    start_time = "20200123"
    make_plot(
        axes,
        "coarse_grid",
        start_time,
        color_fig="k",
        alpha_fig=0.25,
    )
    make_plot(axes, "lagrangian_grid_Ron_Brown", start_time, add_label=True)
    figure_formatting(fig, axes)

    plt.savefig(plotdir + "fig6_moisture_quartiles_lagrangian_grid.png")


def make_plot(
    axes,
    grid,
    start_time,
    linestyle_fig=None,
    color_fig=None,
    alpha_fig=None,
    add_label=False,
):
    for n, resolution in enumerate(resolutions[grid]):
        cubes = iris.load(
            datadir + aggregation_terms_fname.format(start_time, resolution, grid)
        )

        tcw = cubes.extract_cube(variable)

        plt.axes(axes[0])
        for m, cube in enumerate(tcw.slices_over("quartile")):
            if n == 0 and add_label:
                label = "Quartile {}".format(m + 1)
            else:
                label = None

            if linestyle_fig is None:
                linestyle = linestyles[resolution]
            else:
                linestyle = linestyle_fig

            if color_fig is None:
                color = "C{}".format(m)
            else:
                color = color_fig

            if alpha_fig is None:
                alpha = alphas[resolution]
            else:
                alpha = alpha_fig

            if "Ron_Brown" not in grid:
                iplt.plot(
                    cube, linestyle=linestyle, alpha=alpha, color=color, label=label
                )

        plt.axes(axes[1])

        if add_label:
            label = labels[resolution]

        if "Ron_Brown" in grid:
            color = "C3"
            if resolution == "km1p1":
                label = "RHB"
            else:
                label = None
        else:
            color = "k"
        iplt.plot(
            tcw[:, -1] - tcw[:, 0],
            linestyle=linestyle,
            alpha=alpha,
            color=color,
            label=label,
        )


def figure_formatting(fig, axes):
    axes[0].legend(loc="upper left")
    axes[0].set_ylabel("Total column water (kg m$^{-2}$)")
    axes[0].text(
        -0.05, 1.05, "(a)", dict(fontsize="large"), transform=axes[0].transAxes
    )

    axes[1].legend()
    axes[1].xaxis.set_major_formatter(date_format)
    axes[1].set_xlim(datetime.datetime(2020, 2, 2), datetime.datetime(2020, 2, 3))
    axes[1].set_xlabel(r"Time (2$^\mathrm{nd}$ Feb)")
    axes[1].set_ylabel(r"TCW$_\mathrm{q4}$ - TCW$_\mathrm{q1}$")
    axes[1].text(
        -0.05, 1.05, "(b)", dict(fontsize="large"), transform=axes[1].transAxes
    )


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
