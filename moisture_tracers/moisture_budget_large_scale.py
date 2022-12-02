import warnings

from tqdm import tqdm
import iris
from iris.analysis import AreaWeighted

import irise

from moisture_tracers import grey_zone_forecast, datadir
from moisture_tracers import datadir


def main():
    resolutions = ["km1p1", "km2p2", "km4p4"]
    for m, (start_time, grid) in enumerate(
        [
            ("20200201", "lagrangian_grid"),
            ("20200202", "lagrangian_grid"),
            ("20200201", "lagrangian_grid_no_evap"),
            ("20200201", "lagrangian_grid_Ron_Brown"),
        ]
    ):
        print(start_time, grid)
        for n, resolution in enumerate(resolutions):
            fcst = grey_zone_forecast(
                path=datadir + "regridded_vn12/",
                start_time=start_time,
                resolution=resolution,
                lead_times=range(48 + 1),
                grid="{}_large_scale".format(grid),
            )

            results = iris.cube.CubeList()

            if start_time == "20200202":
                lead_times = range(1, 24 + 1)
            else:
                lead_times = range(24, 48 + 1)
            for lead_time in tqdm(lead_times):
                cubes = fcst.set_lead_time(hours=lead_time)
                cubes = cubes.extract(
                    iris.Constraint(time=lambda x: x.point == fcst.current_time)
                )

                f, d = get_fluxes(cubes)
                results.append(f)
                results.append(d)
            fname = "moisture_budget_large_scale_{}_{}_{}.nc".format(
                start_time, resolution, grid
            )
            iris.save(results.merge(), datadir + "diagnostics_vn12/" + fname)


def get_fluxes(cubes):
    rho = cubes.extract_cube("air_density")
    q = cubes.extract_cube("specific_humidity")
    u = cubes.extract_cube("x_wind")
    v = cubes.extract_cube("y_wind")

    moisture = rho * q
    dm_dx = irise.calculus.polar_horizontal(moisture, "x")
    dm_dy = irise.calculus.polar_horizontal(moisture, "y")

    dm_dx_c = dm_dx.regrid(u[:, 1, 1], AreaWeighted())
    dm_dy_c = dm_dy.regrid(v[:, 1, 1], AreaWeighted())

    flx = -(dm_dx_c * u[:, 1, 1].data + dm_dy_c * v[:, 1, 1].data)

    dz = irise.grid.thickness(flx)
    flx_z = (flx * dz).collapsed("altitude", iris.analysis.SUM)
    flx_z.units = "kg m-3 s-1"
    flx_z.rename("moisture_advection")

    du_dx = irise.calculus.polar_horizontal(u, "x")
    dv_dy = irise.calculus.polar_horizontal(v, "y")

    du_dx_c = du_dx.regrid(moisture[:, 1, 1], AreaWeighted())
    dv_dy_c = dv_dy.regrid(moisture[:, 1, 1], AreaWeighted())

    div = du_dx_c + dv_dy_c
    div_m = -(div * moisture[:, 1, 1].data)

    dz = irise.grid.thickness(div_m)
    div_m_z = (div_m * dz).collapsed("altitude", iris.analysis.SUM)
    div_m_z.units = "kg m-3 s-1"
    div_m_z.rename("moisture_divergence")

    return flx_z, div_m_z


if __name__ == "__main__":
    import warnings

    warnings.filterwarnings("ignore")
    main()
