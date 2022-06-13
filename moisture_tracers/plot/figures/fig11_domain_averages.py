from string import ascii_lowercase
import datetime

import iris
from iris.exceptions import ConcatenateError
import iris.plot as iplt
import matplotlib.pyplot as plt

from moisture_tracers import datadir, plotdir
from moisture_tracers.plot.figures import linestyles, labels


diagnostics = [
    ("total_column_water", "Total Column Water (kg m$^{-2}$)"),
    (
        "atmosphere_cloud_liquid_water_content",
        "Total Column Liquid Water (kg m$^{-2}$)",
    ),
    ("stratiform_rainfall_amount", "Hourly Rainfall Amount (kg m$^{-2}$)"),
    ("atmosphere_boundary_layer_thickness", "Boundary Layer Depth (m)"),
    ("toa_outgoing_longwave_flux", "Outgoing Longwave Flux (W m$^{-2}$)"),
    ("toa_outgoing_shortwave_flux", "Outgoing Shortwave Flux (W m$^{-2}$)"),
]

resolutions = ["km1p1", "km2p2", "km4p4"]
start_times = ["0201", "0202"]


def main():
    fig, axes = plt.subplots(3, 2, figsize=(8, 10), sharex="all")

    for n, resolution in enumerate(resolutions):
        for m, start_time in enumerate(start_times):
            cubes = iris.load(
                datadir
                + "diagnostics_vn12/domain_averages_2020{}_{}_lagrangian_grid.nc".format(
                    start_time, resolution
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
                    label = start_time
                else:
                    label = None

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

    axes[0, 0].set_xlim(datetime.datetime(2020, 2, 2), datetime.datetime(2020, 2, 3))
    axes[0, 0].legend()
    axes[0, 1].legend()
    fig.autofmt_xdate()

    plt.savefig(plotdir + "fig11_domain_averages.png")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
