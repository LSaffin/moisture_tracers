from string import ascii_lowercase

import iris.plot as iplt
import matplotlib.pyplot as plt
import cmcrameri

import irise

from moisture_tracers import grey_zone_forecast, datadir, plotdir
from moisture_tracers.plot.figures import projection


labels = [r"$\theta_\mathrm{e}$", r"$q_\mathrm{evap}$"]
kwargs = (
    dict(vmin=345, vmax=360, cmap="magma"),
    dict(vmin=0, vmax=0.0015, cmap="cmc.oslo_r"),
)


def main():
    forecast = grey_zone_forecast(
        path=datadir + "regridded_vn12/",
        start_time="2020-02-01",
        resolution="km1p1",
        lead_times=range(48 + 1),
        grid="lagrangian_grid",
    )

    lead_times = [36, 48]
    variables = ["equivalent_potential_temperature", "microphysics_q"]

    width_factor = 10
    nrows = len(variables)
    ncols = len(lead_times) * width_factor + 2

    plt.figure(figsize=(8, 5))

    for n, variable in enumerate(variables):
        row = n
        for m, lead_time in enumerate(lead_times):
            col = m * width_factor

            cubes = forecast.set_lead_time(hours=lead_time)
            plt.subplot2grid(
                (nrows, ncols), (row, col), colspan=width_factor, projection=projection
            )

            cube = irise.convert.calc(variable, cubes)
            print(variable, cube[0].data.min(), cube[0].data.max())

            im = iplt.pcolormesh(cube[0], **kwargs[n])
            cloud = irise.convert.calc(
                "mass_fraction_of_cloud_liquid_water_in_air",
                cubes,
                levels=("height_above_reference_ellipsoid", [2000]),
            )
            iplt.contour(cloud[0], [1e-5], colors="green", linewidths=2)
            iplt.contour(cloud[0], [1e-5], colors="white", linewidths=0.5)

            ax = plt.gca()
            ax.gridlines()
            ax.coastlines()
            ax.text(
                -0.05,
                1.05,
                "({})".format(ascii_lowercase[n * 2 + m]),
                dict(fontsize="large"),
                transform=ax.transAxes,
            )

            if n == 0:
                if lead_time < 48:
                    day = r" $2^\mathrm{nd}$ Feb"
                else:
                    day = r" $3^\mathrm{rd}$ Feb"

                ax.set_title(forecast.current_time.strftime("%HZ") + day)

        ax = plt.subplot2grid(
            (nrows, ncols),
            (row, col + width_factor),
        )
        cbar = plt.colorbar(im, cax=ax, extend="both", orientation="vertical")
        cbar.set_label(labels[n])

    plt.savefig(plotdir + "fig12_cold_pools.png")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
