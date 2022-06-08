import matplotlib.pyplot as plt

from moisture_tracers import plotdir
from moisture_tracers.plot.figures.fig2_satellite_comparison import make_plot


def main():
    start_time = "20200201"
    grid = "lagrangian_grid"
    resolutions = ["km1p1", "km2p2", "km4p4"]
    lead_times = [30, 36, 42, 48]
    make_plot(start_time, grid, resolutions, lead_times)
    plt.savefig(
        plotdir + "fig4_satellite_comparison_{}_{}.png".format(start_time, grid)
    )


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
