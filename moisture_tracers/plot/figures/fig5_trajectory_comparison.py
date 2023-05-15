import matplotlib.pyplot as plt
import cartopy.crs as ccrs

import irise
from irise.diagnostics.contours import haversine
from pylagranto import trajectory

from moisture_tracers import datadir, plotdir, grey_zone_forecast
from moisture_tracers.plot.figures import linestyles, date_format, add_halo_circle

from matplotlib.lines import Line2D

custom_lines = [
    Line2D([0], [0], color="k", linestyle=linestyles[linestyle])
    for linestyle in linestyles
]

resolutions = ["km1p1", "km2p2", "km4p4"]
simulations = [
    ("20200201", ""),
    ("20200202", ""),
    ("20200201", "_no_evap"),
    ("20200201", "_Ron_Brown"),
]

labels = ["Default", "Late start", "No evap", "RHB"]


def main():
    fig = plt.figure(figsize=(8, 10))

    axes = [
        plt.subplot2grid((2, 1), (0, 0), projection=ccrs.PlateCarree()),
        plt.subplot2grid((2, 1), (1, 0)),
    ]

    tr0 = trajectory.load(
        datadir + "trajectories/trajectories_20200201_km1p1_500m.pkl"
    )[0]
    times = tr0.times[:24]

    for n, (start_time, grid) in enumerate(simulations):
        for m, resolution in enumerate(resolutions):
            tr = trajectory.load(
                datadir
                + "trajectories/trajectories_{}_{}_500m{}.pkl".format(
                    start_time, resolution, grid
                )
            )[0]

            color = "C{}".format(n)
            linestyle = linestyles[resolution]

            if m == 0:
                label = labels[n]
            else:
                label = None

            plt.axes(axes[0])
            if grid == "_Ron_Brown":
                plt.plot(
                    tr.x[24:] - 360,
                    tr.y[24:],
                    linestyle=linestyle,
                    color=color,
                    label=label,
                )
            else:
                plt.plot(
                    tr.x[:24] - 360,
                    tr.y[:24],
                    linestyle=linestyle,
                    color=color,
                    label=label,
                )

            plt.axes(axes[1])
            if start_time != "20200201" or grid != "" or resolution != "km1p1":
                plt.plot(
                    times,
                    haversine([tr0.x[:24], tr0.y[:24]], [tr.x[:24], tr.y[:24]]),
                    color=color,
                    linestyle=linestyle,
                )

    # Plot the boundary of the hectometre-scale domain
    add_domain_box(axes[0], "20200201", "km1p1", "lagrangian_grid", color="k")
    add_domain_box(axes[0], "20200201", "km1p1", "lagrangian_grid_Ron_Brown", color="r")

    leg1 = axes[0].legend(loc="lower right")
    axes[0].legend(custom_lines, ["1.1 km", "2.2 km", "4.4 km"], loc=(0.62, 0.03))
    axes[0].add_artist(leg1)
    axes[0].coastlines()
    axes[0].gridlines()
    add_halo_circle(axes[0])
    axes[0].text(
        -0.05, 1.05, "(a)", dict(fontsize="large"), transform=axes[0].transAxes
    )

    axes[1].set_ylim(0, 45)
    axes[1].xaxis.set_major_formatter(date_format)
    axes[1].set_xlabel(r"Time (2$^\mathrm{nd}$ Feb)")
    axes[1].set_ylabel("Trajectory Separation (km)")
    axes[1].text(
        -0.05, 1.05, "(b)", dict(fontsize="large"), transform=axes[1].transAxes
    )

    plt.savefig(plotdir + "fig5_trajectory_comparison.png")


def add_domain_box(ax, start_time, resolution, grid, **kwargs):
    forecast = grey_zone_forecast(
        datadir + "regridded_vn12/",
        start_time=start_time,
        resolution=resolution,
        grid=grid
    )
    cubes = forecast.set_lead_time(hours=48)
    cube = cubes.extract_cube("total_column_water")
    x = cube.coord("grid_longitude").points - 360
    y = cube.coord("grid_latitude").points

    ax.plot(
        [x[0], x[-1], x[-1], x[0], x[0]], [y[0], y[0], y[-1], y[-1], y[0]], **kwargs
    )


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
