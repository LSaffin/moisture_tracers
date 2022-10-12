"""Put all forecast data on a common grid

Usage:
    regrid_common.py <path> <start_time> <target> [<output_path>]

Arguments:
    <path>
    <start_time>
    <resolution>
    <target>
    <output_path>

Options:
    -h --help
        Show this screen.
"""

import numpy as np

import iris
from iris.analysis import AreaWeighted
from iris.coords import DimCoord

from twinotter.util.scripting import parse_docopt_arguments

from . import grey_zone_forecast


def main(path, start_time, resolution, target, output_path="."):
    forecast = grey_zone_forecast(
        path,
        start_time=start_time,
        resolution=resolution,
        lead_times=range(48 + 1),
        grid=None,
    )

    target_cube = iris.load_cube(target)

    for cubes in forecast:
        print(forecast.lead_time)
        regridder = AreaWeighted()
        newcubes = iris.cube.CubeList()
        for cube in cubes:
            if cube.ndim > 1 and cube.name() not in ["longitude", "latitude"]:
                newcube = cube.regrid(target_cube, regridder)
                newcubes.append(newcube)

        iris.save(
            newcubes,
            "{}/{}_{}_T+{:02d}_common_grid.nc".format(
                output_path,
                forecast.start_time.strftime("%Y%m%dT%H%M"),
                resolution,
                int(forecast.lead_time.total_seconds() // 3600),
            ),
        )


def generate_common_grid(high_res_cube, low_res_cube):
    """We want a cube with the grid spacing of the low_res_cube but restricted to the
    domain of the high_res_cube
    """
    lon = high_res_cube.coord("grid_longitude").points
    lat = high_res_cube.coord("grid_latitude").points

    common_grid_cube = low_res_cube.extract(
        iris.Constraint(
            grid_longitude=lambda x: lon[0] < x < lon[-1],
            grid_latitude=lambda x: lat[0] < x < lat[-1],
        )
    )

    return common_grid_cube


def generate_1km_grid(cube_500m, coarse_factor=2):
    """Generate a 1km grid from the 500m-resolution forecast"""
    # Need to recreate the coordinates as just subsetting the cube keeps the old
    # coordinate bounds which then don't allow area-weighted regridding because they
    # are not contiguous
    # Extract coordinates
    lon = cube_500m.coord("grid_longitude")
    lat = cube_500m.coord("grid_latitude")

    # Get the average coordinate of every n points, where n is the coarse graining
    # factor
    # Chop off where the domain doesn't divide into the coarse factor
    lon_points = chop_coord(lon.points, coarse_factor)
    lat_points = chop_coord(lat.points, coarse_factor)

    lon = DimCoord(
        lon_points,
        standard_name=lon.standard_name,
        units=lon.units,
        attributes=lon.attributes,
        coord_system=lon.coord_system,
        circular=lon.circular,
    )

    lat = DimCoord(
        lat_points,
        standard_name=lat.standard_name,
        units=lat.units,
        attributes=lat.attributes,
        coord_system=lat.coord_system,
        circular=lat.circular,
    )

    lon.guess_bounds()
    lat.guess_bounds()

    cube_1km_grid = iris.cube.Cube(
        data=np.zeros([len(lat.points), len(lon.points)]),
        dim_coords_and_dims=[(lat, 0), (lon, 1)],
    )

    return cube_1km_grid


def generate_large_scale_grid(cube):
    """
    Generate a 3x3 grid that uses the input cube domain as the inner grid point and a
    2x2 grid that is at the 1/2 points in the 3x3 grid
    """
    lon, lon_offset = generate_large_scale_coord(cube.coord("grid_longitude"))
    lat, lat_offset = generate_large_scale_coord(cube.coord("grid_latitude"))

    cube_large_scale = iris.cube.Cube(
        data=np.zeros([len(lat.points), len(lon.points)]),
        dim_coords_and_dims=[(lat, 0), (lon, 1)],
    )

    cube_large_scale_offset = iris.cube.Cube(
        data=np.zeros([len(lat.points), len(lon.points)]),
        dim_coords_and_dims=[(lat, 0), (lon, 1)],
    )

    return cube_large_scale, cube_large_scale_offset


def generate_large_scale_coord(coord):
    coord_centre = coord.points.mean()
    coord_spacing = coord.points.max() - coord.points.min()

    coord_out = DimCoord(
        [coord_centre - coord_spacing, coord_centre, coord_centre + coord_spacing],
        standard_name=coord.standard_name,
        units=coord.units,
        attributes=coord.attributes,
        coord_system=coord.coord_system,
        circular=coord.circular,
    )

    coord_out_offset = DimCoord(
        [coord.points.min(), coord.points.max()],
        standard_name=coord.standard_name,
        units=coord.units,
        attributes=coord.attributes,
        coord_system=coord.coord_system,
        circular=coord.circular,
    )

    coord_out.guess_bounds()
    coord_out_offset.guess_bounds()

    return coord_out, coord_out_offset


def chop_coord(points, coarse_factor):
    offset = len(points) % coarse_factor
    if offset > 0:
        lon_points = points[:-offset]
    else:
        lon_points = points

    return np.mean(lon_points.reshape(-1, coarse_factor), axis=1)


if __name__ == "__main__":
    parse_docopt_arguments(main, __doc__)
