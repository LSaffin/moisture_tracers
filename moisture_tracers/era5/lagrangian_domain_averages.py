import iris

from irise import grid

from moisture_tracers import grey_zone_forecast, datadir, era5


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
        era_grid.append(calculate_vertical_velocity(era_grid))

        for cube in era_grid:
            cube.coord("longitude").guess_bounds()
            cube.coord("latitude").guess_bounds()
            weights = iris.analysis.cartography.area_weights(cube)
            cube_mean = cube.collapsed(["longitude", "latitude"], iris.analysis.MEAN, weights=weights)
            era5_means.append(cube_mean)

    era5_means = era5_means.merge()
    iris.save(era5_means, "era5_lagrangian_means.nc")


def calculate_vertical_velocity(era5_cubes):
    w = era5_cubes.extract_cube("lagrangian_tendency_of_air_pressure").copy()
    z = era5_cubes.extract_cube("geopotential").copy() / 9.81
    z.units = "m"

    z.coord("pressure_level").convert_units("Pa")
    w.coord("pressure_level").convert_units("Pa")

    # Calulate vertical velocity from pressure vertical velocity
    dz_dp = iris.analysis.calculus.differentiate(z, "pressure_level")
    dz_dp = dz_dp.interpolate(
        [("pressure_level", z.coord("pressure_level").points)],
        iris.analysis.Linear()
    )
    dz_dt = dz_dp * w

    # Calculate depth-averaged vertical velocity to 3km
    z_c = z.copy()
    z_c.rename("altitude")
    grid.add_cube_as_coord(dz_dt, z_c)
    dz_dt.coord("altitude").guess_bounds()
    dz = grid.thickness(dz_dt)
    weights = dz * (z.data <= 3000).astype(int)
    w_depth = dz_dt.collapsed(["pressure_level"], iris.analysis.MEAN, weights=weights.data)

    w_depth.rename("upward_air_velocity")

    return w_depth


if __name__ == '__main__':
    import warnings

    warnings.filterwarnings("ignore")

    main()
