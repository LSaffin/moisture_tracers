import datetime

import iris
from iris.analysis import AreaWeighted
import iris.plot as iplt
import matplotlib.pyplot as plt
from dateutil.parser import parse as dateparse

from moisture_tracers import satellite_on_grid, datadir, plotdir
from moisture_tracers.plot.figures import projection

forecast_path = datadir + "simulated_satellite/february2/Baseline/"
forecast_filename = "UMRA3p3_MOapp_{}Z_*scale_2D_Hourly_{}_Baseline_goes16_refl.nc"
satellite_path = datadir + "../../goes/2km_10min/"
resolutions = ["150m", "300m", "500m", "1p1km", "2p2km", "4p4km"]

sat_varname = "refl_0_65um_nom"  # "temp_11_0um_nom"
kwargs = dict(vmin=0, vmax=1, cmap="cmc.nuuk")

lead_times = [35, 38, 42, 45]

resolutions = ["1p1km"]
height_factor = 10
nrows = height_factor * (len(resolutions) + 1) + 2
ncols = len(lead_times)


def main():
    start_time = "20200201"
    grid = "lagrangian_grid"

    plt.figure(figsize=(8, 5))
    make_plot(start_time, grid)

    plt.savefig(
        plotdir + "figA1_simulated_satellite_comparison_{}.png".format(start_time)
    )


def make_plot(start_time, grid):
    t0 = dateparse(start_time)

    if grid == "coarse_grid":
        grid_cube, lons, lats = satellite_on_grid.get_grid(
            datadir + "regridded/20200201T0000_D100m_150m_T+01_coarse_grid.nc"
        )

    for m, lead_time in enumerate(lead_times):
        time = t0 + datetime.timedelta(hours=lead_time)
        print(time)

        time_cs = iris.Constraint(time=lambda x: x.point == time)

        if grid == "lagrangian_grid":
            filename = (
                datadir
                + "regridded_vn12/{}_km1p1_T+{}_lagrangian_grid.nc".format(
                    t0.strftime("%Y%m%dT%H%M"),
                    lead_time,
                )
            )
            grid_cube, lons, lats = satellite_on_grid.get_grid(filename)

        for n, resolution in enumerate(resolutions):
            ax = plt.subplot2grid(
                [nrows, ncols],
                [height_factor * n, m],
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

            if grid == "lagrangian_grid":
                cs = grid_cube.coord("grid_longitude").coord_system

                for coord_name in ["grid_longitude", "grid_latitude"]:
                    coord = cube.coord(coord_name)
                    coord.coord_system = cs
                    coord.guess_bounds()

                cube = cube.regrid(grid_cube, AreaWeighted())

            print(resolution, cube.data.min(), cube.data.max())
            iplt.pcolormesh(cube, **kwargs)

            if n == 0:
                plt.title(time.strftime("%H:%M"))

            if m == 0:
                ax = plt.gca()
                ax.get_yaxis().set_visible(True)
                ax.set_yticks([])
                ax.set_ylabel(resolution)

        # GOES
        ax = plt.subplot2grid(
            [nrows, ncols],
            [height_factor * len(resolutions), m],
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
        satellite_data = cube.copy(data=satellite_data[sat_varname].values) / 100
        print("satellite", satellite_data.data.min(), satellite_data.data.max())
        im = iplt.pcolormesh(satellite_data, **kwargs)

        if m == 0:
            ax.get_yaxis().set_visible(True)
            ax.set_yticks([])
            ax.set_ylabel("GOES ")

    ax = plt.subplot2grid([nrows, ncols], [nrows - 1, 0], colspan=ncols)
    cbar = plt.colorbar(im, cax=ax, extend="both", orientation="horizontal")
    cbar.set_label(r"Reflectivity at 650 nm")


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")

    main()
