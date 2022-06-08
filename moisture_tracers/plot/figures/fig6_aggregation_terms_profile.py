import datetime
from string import ascii_lowercase

import iris
import iris.plot as iplt
import matplotlib.pyplot as plt

from moisture_tracers import datadir, plotdir
from moisture_tracers.plot.figures import linestyles, labels


titles = [
    r"$C = -w_\mathrm{m} \frac{\partial \bar{q}}{\partial z}$",
    r"$A = -(\bar{\mathbf{u}} + \mathbf{u}_\mathrm{m}) \cdot \nabla qt_\mathrm{m}$",
    r"$A_\mathrm{v} = -(\bar{w} + w_\mathrm{m}) \frac{\partial qt_\mathrm{m}}{\partial z}$",
    r"$A_\mathrm{h} = -(\bar{\mathbf{v}} + \mathbf{v}_\mathrm{m}) \cdot \nabla_\mathrm{h} qt_\mathrm{m}$",
    r"$B_\mathrm{v} = \frac{1}{\rho} \frac{\partial}{\partial z} \left[\rho w_\mathrm{cu} qt_\mathrm{cu} \right]_\mathrm{m}$",
    r"$B_\mathrm{h} = - \nabla_\mathrm{h} \cdot \left[v_\mathrm{cu} qt_\mathrm{cu}\right]_\mathrm{m}$",
]

terms = [
    "mesoscale_vertical_advection_of_background_moisture",
    "advection_of_mesoscale_variability",
    "vertical_advection_of_mesoscale_variability",
    "horizontal_advection_of_mesoscale_variability",
    "vertical_cumulus_fluxes",
    "horizontal_cumulus_fluxes",
]

time = datetime.datetime(2020, 2, 2, 10)
cs = iris.Constraint(time=lambda x: x.point == time)
coords = ["time", "altitude"]

aggregation_terms_fname = (
    datadir + "diagnostics_vn12/aggregation_terms_by_quartile_20200201_{}_{}.nc"
)
grid = "lagrangian_grid"


def main():
    fig, axes = plt.subplots(3, 2, sharex="all", sharey="all", figsize=(8, 8))
    for n, resolution in enumerate(["km1p1", "km4p4"]):
        cubes = iris.load(aggregation_terms_fname.format(resolution, grid), cs)
        for m, term in enumerate(terms):
            if term == "advection_of_mesoscale_variability":
                cube = cubes.extract_cube(
                    "vertical_advection_of_mesoscale_variability"
                ) + cubes.extract_cube("horizontal_advection_of_mesoscale_variability")
            else:
                cube = cubes.extract_cube(term)

            ax = plt.axes(axes[m // 2, m % 2])
            for p, subcube in enumerate(cube.slices_over("quartile")):
                if m == 0 and p == 0:
                    label = labels[resolution]
                elif m == 1 and n == 0:
                    label = "Quartile {}".format(p + 1)
                else:
                    label = None

                try:
                    z = subcube.coord("height_above_reference_ellipsoid")
                except iris.exceptions.CoordinateNotFoundError:
                    z = subcube.coord("altitude")

                iplt.plot(
                    subcube,
                    z,
                    color="C{}".format(p),
                    linestyle=linestyles[resolution],
                    label=label,
                    alpha=0.75,
                )

            ax.axvline(color="k")
            ax.set_title(titles[m])
            ax.text(
                -0.05,
                1.05,
                "({})".format(ascii_lowercase[m]),
                dict(fontsize="large"),
                transform=ax.transAxes,
            )

    axes[0, 0].set_ylim(0, 3000)
    axes[0, 0].legend()
    axes[0, 1].legend()

    fig.text(
        0.5, 0.0, "Rate of change in mesoscale moisture anomaly (s$^{-1}$)", ha="center"
    )
    fig.text(0.0, 0.5, "Altitude (m)", rotation="vertical", va="center")

    plt.savefig(plotdir + "fig7_aggregation_terms_profile_t+34.png")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")

    main()
