import iris

from moisture_tracers import grey_zone_forecast, datadir, era5

import warnings
warnings.filterwarnings("ignore")


def main():
    era5_fcst = era5.era5_as_forecast(
        start_time="2020-02-01",
        lead_times=range(48 + 1),
        path=era5.datadir,
    )
    forecast = grey_zone_forecast(
        path=datadir + "regridded_vn12/",
        start_time="2020-02-01",
        resolution="km1p1",
        lead_times=range(24, 48 + 1),
        grid="lagrangian_grid",
    )

    era5_means = iris.cube.CubeList()

    for cubes in forecast:
        print(forecast.current_time)

        era5_at_time = era5_fcst.set_time(forecast.current_time)

        w_fcast = cubes.extract_cube("upward_air_velocity")
        lon = w_fcast.coord("grid_longitude").points - 360
        lat = w_fcast.coord("grid_latitude").points

        area_cs = iris.Constraint(longitude=lambda x: lon.min() <= x <= lon.max(),
                                  latitude=lambda y: lat.min() <= y <= lat.max())

        era_grid = era5_at_time.extract(area_cs)

        for cube in era_grid:
            cube.coord("longitude").guess_bounds()
            cube.coord("latitude").guess_bounds()
            weights = iris.analysis.cartography.area_weights(cube)
            cube_mean = cube.collapsed(["longitude", "latitude"], iris.analysis.MEAN, weights=weights)
            era5_means.append(cube_mean)

    era5_means = era5_means.merge()
    iris.save(era5_means, "era5_lagrangian_means.nc")


if __name__ == '__main__':
    main()
