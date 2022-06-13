from string import ascii_lowercase

import iris
import iris.plot as iplt
from iris.analysis import PERCENTILE
import matplotlib.pyplot as plt
import irise

from moisture_tracers import plotdir
from moisture_tracers.plot.figures import linestyles, labels
from moisture_tracers.plot.figures.fig6_aggregation_terms_profile import (
    aggregation_terms_fname,
    titles,
    terms,
)


grid = "lagrangian_grid"

# Exclude the cumulus-scale fluxes as they are negligible for column averages
terms = terms[:4]

ncols = 2
nrows = len(terms) // 2


def main():
    fig, axes = plt.subplots(nrows, ncols, sharex="all", sharey="all", figsize=(8, 8))
    for n, resolution in enumerate(["km1p1", "km4p4"]):
        cubes = iris.load(aggregation_terms_fname.format(resolution, grid))

        rho = cubes.extract_cube("mesoscale_density")
        dz = irise.grid.thickness(rho)
        for m, term in enumerate(terms):
            if term == "advection_of_mesoscale_variability":
                cube = cubes.extract_cube(
                    "vertical_advection_of_mesoscale_variability"
                ) + cubes.extract_cube("horizontal_advection_of_mesoscale_variability")
            else:
                cube = cubes.extract_cube(term)

            cube_col = (cube * dz.data * rho.data).collapsed(
                ["altitude"], iris.analysis.SUM
            )

            ax = plt.axes(axes[m // 2, m % 2])
            for p, subcube in enumerate(cube_col.slices_over("quartile")):
                if m == 0 and p == 0:
                    label = labels[resolution]
                elif m == 1 and n == 0:
                    label = "Quartile {}".format(p + 1)
                else:
                    label = None

                iplt.plot(
                    subcube * 3600,
                    color="C{}".format(p),
                    linestyle=linestyles[resolution],
                    label=label,
                    alpha=0.75,
                )

            ax.axhline(color="k")
            ax.set_title(titles[m])
            ax.text(
                -0.125,
                1.05,
                "({})".format(ascii_lowercase[m]),
                dict(fontsize="large"),
                transform=ax.transAxes,
            )

    axes[0, 0].legend()
    axes[0, 1].legend(ncol=2)

    fig.autofmt_xdate()
    fig.text(
        0.0,
        0.5,
        "Rate of change in mesoscale moisture anomaly (kg m$^{-2}$ hour$^{-1}$)",
        rotation="vertical",
        va="center",
    )

    plt.savefig(plotdir + "fig7_aggregation_terms_by_column.png")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
