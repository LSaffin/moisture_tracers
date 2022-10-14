import datetime
from dateutil.parser import parse as dateparse

import matplotlib.pyplot as plt
import iris
import iris.plot as iplt
import cmcrameri

from moisture_tracers import datadir, plotdir
from moisture_tracers.plot.figures import labels

varname = "cloud_area_fraction_in_atmosphere_layer_mean"
name_cs = iris.Constraint(name=varname)
time_cs = iris.Constraint(time=lambda cell: cell.point.day >= 2)
fname = datadir + "diagnostics_vn12/domain_averages_{}_{}_{}.nc"

plot_kwargs = dict(vmin=-0.1, vmax=0.1, cmap="cmc.broc_r")
coords = ["time", "height_above_reference_ellipsoid"]


def main():
    make_plot()


def make_plot():
    fig, ax_dict = plt.subplot_mosaic(
        """
        aabb
        aabb
        aabb
        ....
        1111
        ....
        ....
        ccdd
        ccdd
        ccdd
        ....
        eeff
        eeff
        eeff
        ....
        gghh
        gghh
        gghh
        ....
        2222
        """,
        figsize=(8, 10),
    )

    ref = iris.load_cube(
        fname.format("20200201", "km1p1", "coarse_grid"), name_cs & time_cs
    )

    ref.coord("height_above_reference_ellipsoid").convert_units("km")
    im = make_row(
        ref, "20200201", ["D100m_300m", "D100m_500m", "km2p2", "km4p4"],
        "coarse_grid", ax_dict, "cdef"
    )

    plt.axes(ax_dict["a"])
    im = iplt.pcolormesh(
        ref, vmin=0, vmax=0.12, cmap="cmc.davos_r",
        coords=["time", "height_above_reference_ellipsoid"]
    )
    cax = ax_dict["1"]
    cbar = fig.colorbar(im, cax=cax, orientation="horizontal")
    cbar.set_label("Cloud fraction")

    ref = iris.load_cube(
        fname.format("20200201", "km1p1", "lagrangian_grid"), name_cs & time_cs
    )
    im = make_row(ref, "20200202", ["km1p1"], "lagrangian_grid", ax_dict, ["g"])
    im = make_row(ref, "20200201", ["km1p1"], "lagrangian_grid_no_evap", ax_dict, ["h"])

    plt.axes(ax_dict["b"])
    ref.coord("height_above_reference_ellipsoid").convert_units("km")
    iplt.pcolormesh(
        ref, vmin=0, vmax=0.12, cmap="cmc.davos_r",
        coords=["time", "height_above_reference_ellipsoid"]
    )

    t0 = dateparse("20200201")
    ticks = [t0 + datetime.timedelta(hours=dt) for dt in range(24, 48 + 1, 6)]

    for letter in "gh":
        ax = ax_dict[letter]
        ax.set_xticks(ticks)
        ax.set_xticklabels([tick.strftime("%HZ") for tick in ticks])

    for letter in "abcdef":
        ax = ax_dict[letter]
        ax.set_xticks(ticks)
        ax.set_xticklabels(["" for tick in ticks])

    fig.suptitle("Cloud Fraction\nRelative to 1.1km simulation")
    ax_dict["a"].set_ylabel("Height (km)")
    ax_dict["e"].set_ylabel("Height (km)")

    cax = ax_dict["2"]
    cbar = fig.colorbar(im, cax=cax, orientation="horizontal")
    cbar.set_label("Difference in cloud fraction")

    for letter in "bdfh":
        ax_dict[letter].set_yticklabels("")

    # Label panels not by resolution
    ax_dict["a"].set_title("Inner domain")
    ax_dict["b"].set_title("Lagrangian grid")
    ax_dict["g"].set_title("Late start")
    ax_dict["h"].set_title("No evap")

    # Add letters to each panel
    for letter in "abcdefgh":
        ax_dict[letter].text(
            0.01, 1.05, "({})".format(letter), transform=ax_dict[letter].transAxes
        )

    plt.savefig(plotdir + "figx_cloud_fraction.png")


def make_row(ref, start_time, resolutions, grid, ax_dict, letters):
    for n, resolution in enumerate(resolutions):
        print(resolution)
        ax = plt.axes(ax_dict[letters[n]])

        cf = iris.load_cube(
            fname.format(start_time, resolution, grid), name_cs & time_cs
        )
        cf.coord("height_above_reference_ellipsoid").convert_units("km")
        diff = cf - ref.data

        im = iplt.pcolormesh(#
            diff, **plot_kwargs, coords=["time", "height_above_reference_ellipsoid"]
        )
        ax.set_title(labels[resolution])

    return im


if __name__ == '__main__':
    import warnings
    warnings.filterwarnings("ignore")
    main()
