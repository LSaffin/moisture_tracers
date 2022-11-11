from string import ascii_lowercase
import datetime
import pickle

import iris
import numpy as np
from iris.analysis import MEAN
from iris.exceptions import ConcatenateError
import iris.plot as iplt
import matplotlib.pyplot as plt

import irise

from moisture_tracers import datadir, plotdir
from moisture_tracers.plot.figures import linestyles, labels, date_format

with open("advection.pkl", "rb") as f:
    adv = pickle.load(f)
with open("divergence.pkl", "rb") as f:
    conv = pickle.load(f)

diagnostics = [
    ("total_column_water", "Total Column Water (kg m$^{-2}$)"),
    ("moisture_flux_convergence", r"$\nabla_h \cdot (\rho q \mathbf{v})$ (kg m$^{-2}$ hr$^{-1}$)"),
    ("moisture_convergence", r"$\rho q \nabla_h \cdot \mathbf{v}$ (kg m$^{-2}$ hr$^{-1}$)"),
    ("upward_air_velocity", "Vertical Velocity (m s$^{-1}$)"),
    (
        "atmosphere_cloud_liquid_water_content",
        "Total Column Liquid Water (kg m$^{-2}$)",
    ),
    ("stratiform_rainfall_amount", "Hourly Rainfall Amount (kg m$^{-2}$)"),
    ("atmosphere_boundary_layer_thickness", "Boundary Layer Depth (m)"),
    ("toa_outgoing_longwave_flux", "Outgoing Longwave Flux (W m$^{-2}$)"),
    ("toa_outgoing_shortwave_flux", "Outgoing Shortwave Flux (W m$^{-2}$)"),
]

run_labels = ["Default", "Late start", "No evap", "RHB"]

times = [
    datetime.datetime(2020, 2, 2) + datetime.timedelta(hours=n) for n in range(24 + 1)
]


def main():
    fig, axes = plt.subplots(3, 3, figsize=(12, 10), sharex="all")

    for m, (start_time, grid, resolutions) in enumerate(
        [
            ("0201", "lagrangian_grid", ["km1p1", "km2p2", "km4p4"]),
            ("0202", "lagrangian_grid", ["km1p1"]),
            ("0201", "lagrangian_grid_no_evap", ["km1p1"]),
            ("0201", "lagrangian_grid_Ron_Brown", ["km1p1"]),
        ]
    ):
        for n, resolution in enumerate(resolutions):
            fname1 = "domain_averages_2020{}_{}_{}.nc".format(
                start_time, resolution, grid
            )
            fname2 = "moisture_budget_large_scale_2020{}_{}_{}.nc".format(
                start_time, resolution, grid
            )
            cubes = iris.load(
                [datadir + "diagnostics_vn12/" + fname for fname in (fname1, fname2)]
            )

            for i, (diag, title) in enumerate(diagnostics):
                ax = plt.axes(axes[i // 3, i % 3])

                if m == 0 and i == 0:
                    label = labels[resolution]
                elif n == 0 and i == 1:
                    label = run_labels[m]
                else:
                    label = None

                if diag == "moisture_flux_convergence":
                    cube = (cubes.extract_cube("moisture_advection") + cubes.extract_cube("moisture_divergence")) * 3600
                elif diag == "moisture_convergence":
                    cube = cubes.extract_cube("moisture_divergence") * 3600
                else:
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
                        cube = cubes.extract_cube(
                            "TOTAL COLUMN Q (WATER VAPOUR PATH)_mean"
                        )

                    if cube.ndim == 2:
                        # Average wind from 0-3km
                        z_name = "height_above_reference_ellipsoid"
                        cube = cube.extract(
                            iris.Constraint(
                                height_above_reference_ellipsoid=lambda x: x < 3000
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

    plot_era5(axes)

    axes[0, 1].axhline(color="k")
    axes[0, 2].axhline(color="k")
    axes[1, 0].axhline(color="k")
    axes[0, 1].set_ylim(-0.65, 0.25)
    axes[0, 2].set_ylim(-0.65, 0.25)
    axes[2, 0].set_ylim(750, 1150)

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


def plot_era5(axes):
    era5 = iris.load("era5_lagrangian_means.nc")

    kwargs = dict(color="k", lw=3, alpha=0.5)

    tcw = era5.extract_cube("Total column water")
    plt.axes(axes[0, 0])
    iplt.plot(tcw, **kwargs)

    mconv = era5.extract_cube("Vertically integrated moisture divergence")
    plt.axes(axes[0, 1])
    iplt.plot(-mconv, label="ERA5", **kwargs)

    w = iris.load_cube("w_lagrangian_depth_average.nc")
    plt.axes(axes[1, 0])
    iplt.plot(w, **kwargs)

    rain = era5.extract_cube("Mean total precipitation rate")
    plt.axes(axes[1, 2])
    iplt.plot(rain * 3600, **kwargs)

    z_bl = era5.extract_cube("Boundary layer height")
    plt.axes(axes[2, 0])
    iplt.plot(z_bl, **kwargs)

    lw = era5.extract_cube("toa_outgoing_longwave_flux")
    plt.axes(axes[2, 1])
    iplt.plot(-lw / 3600, **kwargs)

    sw_net = era5.extract_cube("toa_net_upward_shortwave_flux")
    sw_in = era5.extract_cube("TOA incident solar radiation")

    sw = sw_in - sw_net
    plt.axes(axes[2, 2])
    iplt.plot(sw / 3600, **kwargs)


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
