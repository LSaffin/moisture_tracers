"""
Plot showing the transition in cloud organisation from the Feb 2 case study

Show cloud images at two lead times for each resolution and compare with satellite
"""

import matplotlib.pyplot as plt
import iris.plot as iplt

from moisture_tracers import grey_zone_forecast, datadir, plotdir


def main():
    start_time = "2020-02-01"
    path = datadir + "regridded/"
    grid = "coarse_grid"

    resolutions = ["D100m_150m", "D100m_300m", "D100m_500m", "km1p1"]
    lead_times = [30, 40]

    fig, axes = plt.subplots(len(lead_times), len(resolutions), figsize=(16, 10))

    # Plot model data
    for n, resolution in enumerate(resolutions):
        forecast = grey_zone_forecast(
            path, start_time=start_time, resolution=resolution, grid=grid
        )
        for m, lead_time in enumerate(lead_times):
            cubes = forecast.set_lead_time(hours=lead_time)
            lw = cubes.extract_cube("toa_outgoing_longwave_flux")

            plt.axes(axes[m, n])
            im = iplt.pcolormesh(lw, vmin=200, vmax=300, cmap="Greys")

            if m == 0:
                plt.title(resolution)
            if n == 0:
                plt.ylabel("T+{}h".format(lead_time))

    # Add a shared colorbar for the model data
    plt.subplots_adjust(bottom=0.2)
    cax = plt.axes([0.1, 0.1, 0.8, 0.05])
    fig.colorbar(im, cax=cax, orientation="horizontal")

    # TODO: Plot satellite data
    pass

    plt.savefig(plotdir + "sugar_to_flowers_transition.png")


if __name__ == '__main__':
    main()
