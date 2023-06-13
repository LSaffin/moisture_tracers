"""Full data processing of simulations with parametrized convection for producing
figures in moisture_tracers.plot.figures_parametrized_convection
"""

import warnings

import iris
from iris.cube import CubeList

import pylagranto.trajectory

from moisture_tracers import (
    datadir,
    regridded_filename,
    grey_zone_forecast,
    regrid_common,
    trajectory,
    regrid_trajectory,
    aggregation_terms,
    domain_averages,
)

regridded_path = datadir + "regridded_conv/"
diags_path = datadir + "diagnostics_conv/"

start_time = "20200201"
resolutions = ["km4p4", "km10"]
model_setups = ["GAL8", "CoMorphA"]

x0, y0, z0, t0 = 302.5, 13.5, 950, 48
trajectory_zcoord = "pressure"


def main():
    warnings.filterwarnings("ignore")

    # 0. Create shared cube to generate a common grid
    # 10km grid spacing using the size of the inner domain
    target = datadir + "inner_domain_10km_grid.nc"
    high_res_cube = iris.load_cube(
        datadir + "D100m_500m/model-diagnostics_20200201T0000_T+35.nc",
        "surface_air_pressure"
    )[0]
    # RAL3 data is grid_longitude x grid_latitude and shows as being a rotated grid but
    # has zero rotation, so just rename the coordinate to allow the common grid to be
    # generated
    high_res_cube.coord("grid_longitude").rename("longitude")
    high_res_cube.coord("grid_latitude").rename("latitude")

    low_res_cube = iris.load_cube(
        "datadir" + "km10/20200201T0000Z_EUREC4A_ICfinal1km_km10_GAL8_pvera036.pp",
        "surface_air_pressure"
    )[0]
    cube = regrid_common.generate_common_grid(high_res_cube, low_res_cube)
    iris.save(cube, target)

    for model_setup in model_setups:
        print(model_setup)
        for resolution in resolutions:
            print(resolution)
            forecast = grey_zone_forecast(
                path=datadir,
                start_time=start_time,
                resolution=resolution,
                lead_times=range(3, 48 + 1, 3),
                grid=None,
                output_type="RMED",
                model_setup=model_setup,
            )

            # 1. Calculate trajectories from full domain
            trajectory_filename = (
                f"trajectory_{start_time}_{resolution}_{model_setup}_"
                f"{x0}E_{y0}N_{z0}hPa_T+{t0}.pkl"
            )

            traout = trajectory.calculate_trajectory(
                forecast, x0, y0, z0, t0, trajectory_zcoord
            )
            traout.save(datadir + "trajectories/" + trajectory_filename)

            # 2. Regrid data following trajectory
            traout = pylagranto.trajectory.load(datadir + "trajectories/" + trajectory_filename)
            common_grid = iris.load_cube(target)

            for newcubes in regrid_trajectory.from_forecast(forecast, traout, grid=common_grid):
                iris.save(newcubes, regridded_path + regridded_filename.format(
                    start_time=start_time + "T0000",
                    resolution=model_setup + "_" + resolution,
                    lead_time=int(forecast.lead_time.total_seconds() // 3600),
                    grid="lagrangian_grid",
                ))

            # 3. Moisture Quartiles
            forecast_lagrangian = grey_zone_forecast(
                path=datadir + "regridded_conv/",
                start_time=start_time,
                resolution=f"{model_setup}_{resolution}",
                lead_times=range(3, 48 + 1, 3),
                grid="lagrangian_grid",
            )

            tcw_by_quartile = CubeList()
            for cubes in forecast_lagrangian:
                tcw = cubes.extract_cube("total_column_water")
                tcw_by_quartile.append(
                    aggregation_terms.average_by_quartile(tcw, [tcw], None)[0]
                )
            tcw_by_quartile = tcw_by_quartile.merge_cube()
            iris.save(
                tcw_by_quartile,
                diags_path + f"aggregation_terms_by_quartile_"
                             f"{start_time}_"
                             f"{forecast_lagrangian.resolution}_"
                             f"{forecast_lagrangian.grid}.nc"
            )

            # 4. Domain Averages
            results = domain_averages.generate(forecast_lagrangian)
            iris.save(
                results,
                diags_path + f"domain_averages_"
                             f"{start_time}_"
                             f"{forecast_lagrangian.resolution}_"
                             f"{forecast_lagrangian.grid}.nc"
            )


if __name__ == "__main__":
    main()
