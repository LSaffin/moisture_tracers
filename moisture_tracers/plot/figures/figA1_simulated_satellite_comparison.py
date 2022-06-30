import datetime

import iris
from iris.analysis import AreaWeighted
import iris.plot as iplt
import matplotlib.pyplot as plt
from dateutil.parser import parse as dateparse

from moisture_tracers import satellite_on_grid, datadir, plotdir
from moisture_tracers.plot.figures import projection, labels, satellite_plot_kwargs

forecast_path = datadir + "simulated_satellite/february2/Baseline/"
forecast_filename = "UMRA3p3_MOapp_{}Z_*scale_2D_Hourly_{}_Baseline_goes16_brt.nc"
satellite_path = datadir + "../../goes/2km_10min/"
resolutions = ["150m", "300m", "500m", "1p1km", "2p2km", "4p4km"]

sat_varname = "temp_11_0um_nom"

lead_times = [35, 38, 42, 45]

height_factor = 5
nrows = height_factor * (len(resolutions) + 1) + 2
ncols = len(lead_times)


def main():
    start_time = "20200201"
    grid = "coarse_grid"

    plt.figure(figsize=(8, nrows / 3))
    make_plot(start_time, grid)

    plt.savefig(
        plotdir + "figA1_simulated_satellite_comparison_{}.png".format(start_time)
    )


def make_plot(start_time, grid):
    t0 = dateparse(start_time)

    grid_cube, lons, lats = satellite_on_grid.get_grid(
        datadir + "regridded_vn12/20200201T0000_km1p1_T+48_lagrangian_grid.nc"
    )

    for m, lead_time in enumerate(lead_times):
        time = t0 + datetime.timedelta(hours=lead_time)
        print(time)

        time_cs = iris.Constraint(time=lambda x: x.point == time)

        for n, resolution in enumerate(resolutions):
            plt.subplot2grid(
                (nrows, ncols),
                (height_factor * n, m),
                rowspan=height_factor,
                projection=projection,
            )

            cube = iris.load_cube(
                forecast_path
                + forecast_filename.format(
                    t0.strftime("%Y%m%dT%H%M"),
                    resolution,
                ),
                time_cs,
            )

            for coord in ["grid_longitude", "grid_latitude"]:
                cube.coord(coord).guess_bounds()
                cube.coord(coord).coord_system = grid_cube.coord(coord).coord_system

            cube = cube.regrid(grid_cube, AreaWeighted())
            print(resolution, cube.data.min(), cube.data.max())
            iplt.pcolormesh(cube, **satellite_plot_kwargs)

            if n == 0:
                plt.title(time.strftime("%H:%M"))

            if m == 0:
                ax = plt.gca()
                ax.get_yaxis().set_visible(True)
                ax.set_yticks([])
                ax.set_ylabel(labels[resolution])

        # GOES
        ax = plt.subplot2grid(
            (nrows, ncols),
            (height_factor * len(resolutions), m),
            rowspan=height_factor,
            projection=projection,
        )

        satellite_data = satellite_on_grid.goes_regridded(
            satellite_path,
            time,
            lons,
            lats,
            sat_varname,
        )
        satellite_data = grid_cube.copy(data=satellite_data[sat_varname].values)
        print("satellite", satellite_data.data.min(), satellite_data.data.max())
        im = iplt.pcolormesh(satellite_data, **satellite_plot_kwargs)

        if m == 0:
            ax.get_yaxis().set_visible(True)
            ax.set_yticks([])
            ax.set_ylabel("GOES ")

    ax = plt.subplot2grid((nrows, ncols), (nrows - 1, 0), colspan=ncols)
    cbar = plt.colorbar(im, cax=ax, extend="both", orientation="horizontal")
    cbar.set_label(r"11 $\mu$m brightness temperature (K)")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
