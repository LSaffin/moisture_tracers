"""Put all forecast data on a common grid

Usage:
    regrid_common.py <path> <year> <month> <day> <target>

Arguments:
    <path>
    <year>
    <month>
    <day>
    <target>

Options:
    -h --help
        Show this screen.
"""
import datetime
import docopt

import numpy as np

import iris
from iris.coords import DimCoord

from . import grey_zone_forecast


def main():
    args = docopt.docopt(__doc__)

    start_time = datetime.datetime(
        year=int(args["<year>"]),
        month=int(args["<month>"]),
        day=int(args["<day>"]),
    )
    forecast = grey_zone_forecast(
        args["<path>"], start_time=start_time, lead_times=range(1, 48+1)
    )

    target_cube = iris.load_cube(args["<target>"])

    for cubes in forecast:
        print(forecast.lead_time)
        regridder = iris.analysis.AreaWeighted()
        newcubes = iris.cube.CubeList()
        for cube in cubes:
            if cube.ndim > 1 and cube.name() not in ["longitude", "latitude"]:
                newcube = cube.regrid(target_cube, regridder)
                newcubes.append(newcube)

        iris.save(newcubes, "{}_T+{:02d}_common_grid.nc".format(
            forecast.start_time.strftime("%Y%m%dT%H%M"),
            int(forecast.lead_time.total_seconds() // 3600)),
                  )


def generate_common_grid(high_res_cube, low_res_cube):
    """We want a cube with the grid spacing of the low_res_cube but restricted to the
    domain of the high_res_cube
    """
    lon = high_res_cube.coord("grid_longitude").points
    lat = high_res_cube.coord("grid_latitude").points

    common_grid_cube = low_res_cube.extract(iris.Constraint(
        grid_longitude=lambda x: lon[0] < x < lon[-1],
        grid_latitude=lambda x: lat[0] < x < lat[-1],
    ))

    return common_grid_cube


def generate_1km_grid(cube_500m):
    """Generate a 1km grid from the 500m-resolution forecast
    """
    # Need to recreate the coordinates as just subsetting the cube keeps the old
    # coordinate bounds which then don't allow area-weighted regridding because they
    # are not contiguous
    lon = cube_500m.coord("grid_longitude")
    lon = DimCoord(
        lon.points[::2],
        standard_name=lon.standard_name,
        units=lon.units,
        attributes=lon.attributes,
        coord_system=lon.coord_system,
        circular=lon.circular,
    )
    lat = cube_500m.coord("grid_latitude")
    lat = DimCoord(
        lat.points[::2],
        standard_name=lat.standard_name,
        units=lat.units,
        attributes=lat.attributes,
        coord_system=lat.coord_system,
        circular=lat.circular,
    )

    lon.guess_bounds()
    lat.guess_bounds()

    cube_1km_grid = iris.cube.Cube(data=np.zeros([len(lat.points), len(lon.points)]),
                                   dim_coords_and_dims=[(lat, 0), (lon, 1)])

    return cube_1km_grid


if __name__ == '__main__':
    main()
