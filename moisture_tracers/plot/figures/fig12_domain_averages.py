from string import ascii_lowercase
import datetime

import iris
from iris.analysis import MEAN
from iris.exceptions import ConcatenateError
import iris.plot as iplt
import matplotlib.pyplot as plt

import irise

from moisture_tracers import datadir, plotdir
from moisture_tracers.plot.figures import linestyles, labels, date_format


diagnostics = [
    ("total_column_water", "Total Column Water (kg m$^{-2}$)"),
    ("upward_air_velocity", "Vertical Velocity (m s$^{-1}$)"),
    (
        "atmosphere_cloud_liquid_water_content",
        "Total Column Liquid Water (kg m$^{-2}$)",
    ),
    ("stratiform_rainfall_amount", "Hourly Rainfall Amount (kg m$^{-2}$)"),
    # ("atmosphere_boundary_layer_thickness", "Boundary Layer Depth (m)"),
    ("toa_outgoing_longwave_flux", "Outgoing Longwave Flux (W m$^{-2}$)"),
    ("toa_outgoing_shortwave_flux", "Outgoing Shortwave Flux (W m$^{-2}$)"),
]

resolutions = ["km1p1", "km2p2", "km4p4"]
start_times = ["0201", "0202"]

run_labels = ["Default", "Late start", "No evap"]


def main():
    fig, axes = plt.subplots(3, 2, figsize=(8, 10), sharex="all")

    for n, resolution in enumerate(resolutions):
        for m, (start_time, grid) in enumerate(
            [
                ("0201", "lagrangian_grid"),
                ("0202", "lagrangian_grid"),
                ("0201", "lagrangian_grid_no_evap"),
            ]
        ):
            cubes = iris.load(
                datadir
                + "diagnostics_vn12/domain_averages_2020{}_{}_{}.nc".format(
                    start_time,
                    resolution,
                    grid,
                )
            )

            for i, (diag, title) in enumerate(diagnostics):
                ax = plt.axes(axes[i // 2, i % 2])

                try:
                    cube = cubes.extract(diag + "_mean")
                    try:
                        cube = cube.concatenate_cube()
                    except ConcatenateError:
                        for c in cube:
                            c.coord("time").var_name = "time"
                            c.var_name = c.name()
                            c.remove_coord("grid_longitude")
                            c.remove_coord("grid_latitude")
                        cube = cube.concatenate_cube()
                except ValueError:
                    print(diag)
                    cube = cubes.extract_cube("TOTAL COLUMN Q (WATER VAPOUR PATH)_mean")

                if m == 0 and i == 0:
                    label = labels[resolution]
                elif n == 0 and i == 1:
                    label = run_labels[m]
                else:
                    label = None

                if cube.ndim == 2:
                    # Average wind from 0-2km
                    z_name = "height_above_reference_ellipsoid"
                    cube = cube.extract(
                        iris.Constraint(
                            height_above_reference_ellipsoid=lambda x: x < 2000
                        )
                    )
                    dz = irise.grid.thickness(cube[0], z_name=z_name)
                    cube = cube.collapsed([z_name], MEAN, weights=dz.data)
                iplt.plot(
                    cube,
                    color="C{}".format(m),
                    linestyle=linestyles[resolution],
                    label=label,
                )

                if n == 0 and m == 0:
                    ax.set_title(title)
                    ax.text(
                        -0.125,
                        1.05,
                        "({})".format(ascii_lowercase[i]),
                        dict(fontsize="large"),
                        transform=ax.transAxes,
                    )

    axes[0, 1].axhline(color="k")
    axes[2, 1].set_ylim(50, 290)

    axes[0, 0].set_xlim(datetime.datetime(2020, 2, 2), datetime.datetime(2020, 2, 3))
    axes[0, 0].xaxis.set_major_formatter(date_format)
    fig.text(0.5, 0.05, r"Time (2$^\mathrm{nd}$ Feb)", ha="center")

    lg1 = axes[0, 0].legend(loc="lower right")
    for handle in lg1.legendHandles:
        handle.set_color("k")

    h, l = axes[0, 1].get_legend_handles_labels()
    axes[0, 0].legend(h, l, loc="upper left")
    axes[0, 0].add_artist(lg1)

    plt.savefig(plotdir + "fig12_domain_averages.png")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
