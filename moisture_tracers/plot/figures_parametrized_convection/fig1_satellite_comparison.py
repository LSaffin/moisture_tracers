import iris.plot as iplt
import matplotlib.pyplot as plt
import cmcrameri

from moisture_tracers.plot.figures import lw_flux_plot_kwargs
from moisture_tracers.plot.figures.fig2_satellite_comparison import cbar_label
from moisture_tracers.plot.figures_parametrized_convection import plotdir, forecasts

import warnings
warnings.filterwarnings("ignore")

labels_fc = [
    "RAL3\n1.1km",
    "RAL3\n4.4km",
    "CoMorph\n4.4km",
    "CoMorph\n10km",
    "GAL8\n4.4km",
    "GAL8\n10km"
]

height_factor = 5


def main():
    varname = "toa_outgoing_longwave_flux"
    times = range(30, 48 + 1, 6)
    show_comparison(varname, forecasts, times, cbar_label, **lw_flux_plot_kwargs)
    plt.savefig(plotdir + "comorph_comparison_lw.png")


def show_comparison(varname, forecasts_to_plot, times, cbar_labl, **plot_kwargs):
    nf = len(forecasts_to_plot)
    nt = len(times)

    nrows = height_factor * nf + 1

    plt.figure(figsize=(8, nrows / 4))

    for n, time in enumerate(times):
        print(time)
        for m, forecast in enumerate(forecasts_to_plot):
            row = height_factor * m
            plt.subplot2grid((nrows, nt), (row, n), rowspan=height_factor)

            cubes = forecast.set_lead_time(hours=time)
            cube_fc = cubes.extract_cube(varname)
            im = iplt.pcolormesh(cube_fc, **plot_kwargs)

            if m == 0:
                plt.title(f"{time%24:02d}Z")

            # Put the resolution at the left side of each row
            if n == 0:
                # Need to re-grab the axis because iplt.pcolormesh creates a new one
                ax = plt.gca()
                ax.get_yaxis().set_visible(True)
                ax.set_yticks([])
                ax.set_ylabel(labels_fc[m])

    ax = plt.subplot2grid((nrows, nt), (nrows - 1, 0), colspan=nt)
    cbar = plt.colorbar(im, cax=ax, orientation="horizontal")
    cbar.set_label(cbar_labl)


if __name__ == '__main__':
    main()
