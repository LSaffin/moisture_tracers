import iris
from iris.analysis import AreaWeighted
import iris.plot as iplt
import matplotlib.pyplot as plt
import cmcrameri

from moisture_tracers import grey_zone_forecast, datadir
from moisture_tracers.plot.figures import lw_flux_plot_kwargs, projection
from moisture_tracers.plot.figures.fig2_satellite_comparison import cbar_label
from moisture_tracers.plot.figures_parametrized_convection import plotdir

import warnings
warnings.filterwarnings("ignore")

labels_fc = ["RAL3\n1.1km", "RAL3\n4.4km"]
labels_co = ["CoMorph\n4.4km", "CoMorph\n10km", "GAL8\n4.4km",  "GAL8\n10km"]

height_factor = 5


def main():
    varname = "toa_outgoing_longwave_flux"
    lead_times = range(24, 48 + 1, 6)

    cubes = []
    # "{start_time}Z_EUREC4A_ICfinal1km_{resolution}_{model_setup}_pver*{lead_time:03d}.pp"
    for model_setup in ["CoMorphA", "GAL8"]:
        for resolution in ["km4p4", "km10"]:
            cubes.append(iris.load_cube(
                datadir + "{}/20200201T0000Z_EUREC4A_ICfinal1km_{}_{}_pvera*.pp".format(
                    resolution, resolution, model_setup
                ),
                varname
            ))

    forecasts = []
    for resolution in ["km1p1", "km4p4"]:
        forecasts.append(grey_zone_forecast(
            path=datadir + "regridded_vn12/",
            start_time="2020-02-01",
            resolution=resolution,
            lead_times=lead_times,
            grid="lagrangian_grid",
        ))

    times = forecasts[0].times
    show_comparison(cubes, varname, forecasts, times, **lw_flux_plot_kwargs)
    plt.savefig(plotdir + "comorph_comparison_lw.png")


def show_comparison(cubes_co, varname, forecasts, times, **plot_kwargs):
    nf = len(forecasts)
    nc = len(cubes_co)
    nt = len(times)

    nrows = height_factor * (nf + nc) + 1

    plt.figure(figsize=(8, nrows / 3))

    for n, time in enumerate(times):
        print(time)
        for m, forecast in enumerate(forecasts):
            row = height_factor * m
            plt.subplot2grid(
                (nrows, nt),
                (row, n),
                rowspan=height_factor,
                projection=projection,
            )

            cubes = forecast.set_time(time)
            cube_fc = cubes.extract_cube(varname)
            iplt.pcolormesh(cube_fc, **plot_kwargs)

            if m == 0:
                plt.title(time.strftime("%HZ"))

            # Put the resolution at the left side of each row
            if n == 0:
                # Need to re-grab the axis because iplt.pcolormesh creates a new one
                ax = plt.gca()
                ax.get_yaxis().set_visible(True)
                ax.set_yticks([])
                ax.set_ylabel(labels_fc[m])

        for m2, cube_co in enumerate(cubes_co):
            row = height_factor * (m2 + nf)
            plt.subplot2grid(
                (nrows, nt),
                (row, n),
                rowspan=height_factor,
                projection=projection,
            )

            cube_co = cube_co.extract(iris.Constraint(
                time=lambda cell: cell.point.hour == forecast.current_time.hour and
                                  cell.point.day == forecast.current_time.day
            ))
            for axis in ["x", "y"]:
                coord = cube_co.coord(axis=axis)
                coord.guess_bounds()
                coord.coord_system = cube_fc.coord(axis=axis).coord_system
                coord.rename(cube_fc.coord(axis=axis).name())
            cube_co = cube_co.regrid(cube_fc, AreaWeighted())

            im = iplt.pcolormesh(cube_co, **plot_kwargs)

            # Put the resolution at the left side of each row
            if n == 0:
                # Need to re-grab the axis because iplt.pcolormesh creates a new
                # one
                ax = plt.gca()
                ax.get_yaxis().set_visible(True)
                ax.set_yticks([])
                ax.set_ylabel(labels_co[m2])

    ax = plt.subplot2grid((nrows, nt), (nrows - 1, 0), colspan=nt)
    cbar = plt.colorbar(im, cax=ax, orientation="horizontal")
    cbar.set_label(cbar_label)


if __name__ == '__main__':
    main()
