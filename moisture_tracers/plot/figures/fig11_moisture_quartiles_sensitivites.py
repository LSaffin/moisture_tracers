import datetime
from string import ascii_lowercase

import matplotlib.pyplot as plt

from moisture_tracers import plotdir
from moisture_tracers.plot.figures import date_format
from moisture_tracers.plot.figures.fig6_moisture_quartiles import make_plot


def main():
    fig, axes = plt.subplots(2, 2, sharex="all", sharey="row", figsize=(8, 5))
    axes_pairs = [[axes[0, 0], axes[1, 0]], [axes[0, 1], axes[1, 1]]]

    for axes_pair in axes_pairs:
        make_plot(
            axes_pair,
            "lagrangian_grid",
            "20200201",
            color_fig="k",
            alpha_fig=0.25,
        )

    make_plot(axes_pairs[0], "lagrangian_grid", "20200202", add_label=True)
    axes[0, 0].set_title("Late start")
    make_plot(axes_pairs[1], "lagrangian_grid_no_evap", "20200201", add_label=True)
    axes[0, 1].set_title("No evap")

    axes[0, 0].legend(loc="upper left")
    axes[0, 0].set_ylabel("Total column water (kg m$^{-2}$)")

    axes[1, 0].legend()
    axes[1, 0].xaxis.set_major_formatter(date_format)
    axes[0, 0].set_xlim(datetime.datetime(2020, 2, 2), datetime.datetime(2020, 2, 3))
    fig.text(0.5, 0.0, r"Time (2$^\mathrm{nd}$ Feb)", ha="center")
    axes[1, 0].set_ylabel(r"TCW$_\mathrm{q4}$ - TCW$_\mathrm{q1}$")

    for n in range(4):
        axes[n // 2, n % 2].text(
            -0.05,
            1.05,
            "({})".format(ascii_lowercase[n]),
            dict(fontsize="large"),
            transform=axes[n // 2, n % 2].transAxes,
        )

    plt.savefig(plotdir + "fig11_moisture_quartiles_sensitivities.png")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
