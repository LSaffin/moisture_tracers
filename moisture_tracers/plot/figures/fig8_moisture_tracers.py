import datetime
from string import ascii_lowercase

import iris
import iris.plot as iplt
from iris.analysis import PERCENTILE
import matplotlib.pyplot as plt

import irise

from moisture_tracers import datadir, plotdir
from moisture_tracers.plot.figures import linestyles, labels

z_name = "altitude"


def main():
    terms = [
        "specific_humidity",
        "advection_only_q",
        "boundary_layer_q",
        "stratiform_rainfall_amount",
    ]

    times = iris.Constraint(
        time=lambda cell: datetime.datetime(2020, 2, 2)
        <= cell.point
        <= datetime.datetime(2020, 2, 3)
    )

    for n, resolution in enumerate(["km1p1", "km2p2", "km4p4"]):
        print(resolution)
        fig, axes = plt.subplots(2, 2, sharex="all", sharey="all", figsize=(8, 5))

        cubes = iris.load(
            datadir
            + "diagnostics_vn12/variables_by_quartile_20200201_{}_lagrangian_grid.nc".format(
                resolution
            ),
            times,
        )
        rho = cubes.extract_cube("air_density_mean")

        try:
            dz = irise.grid.thickness(rho, z_name="altitude")
        except iris.exceptions.CoordinateNotFoundError:
            dz = irise.grid.thickness(rho, z_name="height_above_reference_ellipsoid")

        mass = rho * dz

        for m, term in enumerate(terms):
            cube = cubes.extract_cube(term + "_mean")

            if cube.ndim == 3:
                cube = (cube * mass).collapsed([z_name], iris.analysis.SUM)
                cube = cube[1:] - cube[:-1].data
            else:
                cube = -cube

            ax = plt.axes(axes[m // 2, m % 2])
            for p, subcube in enumerate(cube.slices_over("quartile")):
                if m == 2:
                    label = "Quartile {}".format(p + 1)
                else:
                    label = None

                iplt.plot(
                    subcube,
                    color="C{}".format(p),
                    label=label,
                    linestyle=linestyles[resolution],
                )
                ax.set_title(term)

            ax.text(
                -0.05,
                1.05,
                "({})".format(ascii_lowercase[m]),
                dict(fontsize="large"),
                transform=ax.transAxes,
            )
            ax.axhline(color="k")

        axes[1, 0].legend(ncol=2)

        axes[0, 0].set_xlim(
            datetime.datetime(2020, 2, 2), datetime.datetime(2020, 2, 3)
        )

        fig.text(
            0.0,
            0.5,
            "Change in total column water (kg m$^{-2}$ hour$^{-1}$)",
            rotation="vertical",
            va="center",
        )
        fig.autofmt_xdate()

        plt.savefig(
            plotdir + "fig8_moisture_tracer_aggregation_{}.png".format(resolution)
        )


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
