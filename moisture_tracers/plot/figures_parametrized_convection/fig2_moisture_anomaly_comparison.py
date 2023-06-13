"""
Same as figure 1, but for total column water
"""

import matplotlib.pyplot as plt

from moisture_tracers.plot.figures_parametrized_convection import plotdir, forecasts
from moisture_tracers.plot.figures_parametrized_convection.fig1_satellite_comparison \
    import show_comparison

import warnings

warnings.filterwarnings("ignore")


def main():
    show_comparison(
        varname="total_column_water",
        forecasts_to_plot=forecasts,
        times=range(24, 48 + 1, 6),
        cbar_labl="Total Column Water (kg m$^{-2}$)",
        vmin=20,
        vmax=50,
        cmap="cmc.oslo_r"
    )
    plt.savefig(plotdir + "fig2_comorph_comparison_tcw.png")


if __name__ == '__main__':
    main()
