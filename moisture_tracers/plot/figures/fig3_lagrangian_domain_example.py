"""
Show the quasi-Lagrangian domains extracted from a larger domain simulation at
a set of different lead times and overlay the trajectory
"""

import iris.plot as iplt
import matplotlib.pyplot as plt
import cmcrameri

from pylagranto import trajectory
from twinotter.external import eurec4a

from moisture_tracers import datadir, plotdir, grey_zone_forecast


lead_times = [6, 30, 48]
forecast = grey_zone_forecast(
    path=datadir + "regridded_vn12/",
    start_time="2020-02-01",
    resolution="km1p1",
    lead_times=range(48 + 1),
    grid="lagrangian_grid",
)
variable = "total_column_water"


def main():
    plt.figure(figsize=(8, 6))

    tr = trajectory.load(datadir + "trajectories/trajectories_20200201_km1p1_500m.pkl")

    for lead_time in lead_times:
        cubes = forecast.set_lead_time(hours=lead_time)
        cube = cubes.extract_cube(variable)

        iplt.pcolormesh(cube, vmin=18, vmax=35, cmap="cmc.oslo_r")

        print(lead_time, cube.data.min(), cube.data.max())

        # For some reason the x coordinate ends up offset by 180
        plt.plot(
            tr[0].x[48 - lead_time] - 180, tr[0].y[48 - lead_time], "kx", alpha=0.75
        )

        x = cube.coord("grid_longitude").points
        y = cube.coord("grid_latitude").points
        plt.text(x.min() - 180, y.max(), "T+{}h".format(lead_time))

    cbar = plt.colorbar(orientation="horizontal")
    cbar.set_label("Total column water (kg m$^{-2}$)")

    plt.plot(tr[0].x - 180, tr[0].y, "--k", alpha=0.75)

    ax = plt.gca()
    ax.gridlines()
    ax.coastlines()
    eurec4a.add_halo_circle(ax, alpha=0.75, lw=3)

    plt.savefig(plotdir + "fig4_lagrangian_domain_example_1p1km.png")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")

    main()
