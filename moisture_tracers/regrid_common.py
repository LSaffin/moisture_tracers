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

import iris

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


if __name__ == '__main__':
    main()

