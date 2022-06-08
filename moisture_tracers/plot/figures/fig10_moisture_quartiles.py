import matplotlib.pyplot as plt

from moisture_tracers import plotdir
from moisture_tracers.plot.figures.fig5_moisture_quartiles import (
    make_plot,
    figure_formatting,
)


def main():
    fig, axes = plt.subplots(2, 1, sharex="all", figsize=(8, 8))

    make_plot(
        axes,
        "lagrangian_grid",
        "20200201",
        linestyle_fig="-",
        color_fig="k",
        alpha_fig=0.25,
    )
    make_plot(axes, "lagrangian_grid", "20200202", add_label=True)
    figure_formatting(fig, axes)

    plt.savefig(plotdir + "fig10_moisture_quartiles_lagrangian_grid_late_start.png")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
