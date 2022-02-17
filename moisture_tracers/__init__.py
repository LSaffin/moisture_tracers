"""Top-level package for moisture_tracers."""

__author__ = """Leo Saffin"""
__email__ = 'l.saffin@leeds.ac.uk'
__version__ = '0.1.0'


import datetime

from dateutil.parser import parse as dateparse

from irise.interpolate import remap_3d
from irise.forecast import Forecast

from myscripts.projects.eurec4a.moisture_tracers import datadir, plotdir

# Filename Patterns
# model-variables_YYYYMMDDTHHMM_T+HH.nc and
# moisture-tracers_YYYYMMDDTHHMM_T+HH.nc
model_filename = "*_{start_time}_T+{lead_time:02d}.nc"

# YYYYMMDDTHHMM_DomainResolution_T+HH_coarse_grid.nc
regridded_filename = "{start_time}_{resolution}_T+{lead_time:02d}_{grid}.nc"


def grey_zone_forecast(
        path=datadir + "regridded/",
        start_time="2020-02-01",
        resolution="km4p4",
        lead_times=range(48+1),
        grid="coarse_grid",
):
    """Return an irise.forecast.Forecast for an individual grey-zone simulation

    Args:
        path (str):
        start_time (datetime.datetime | str):
        resolution (str):
        lead_times (iterable): Sequence of lead times (in hours) in the requested
            simulation. Default is every hour from 1 to 48
        grid (str | None):

    Returns:
        irise.forecast.Forecast:
    """
    if isinstance(start_time, str):
        start_time = dateparse(start_time)

    start_time_str = start_time.strftime("%Y%m%dT%H%M")

    if grid is None:
        mapping = {
            start_time + datetime.timedelta(hours=dt): [
                path + model_filename.format(
                    start_time=start_time_str,
                    lead_time=max(0, dt-1)
                ),
            ] for dt in lead_times
        }

    else:
        mapping = {
            start_time + datetime.timedelta(hours=dt): [
                path + regridded_filename.format(
                    start_time=start_time_str,
                    resolution=resolution,
                    lead_time=dt,
                    grid=grid,
                ),
            ] for dt in lead_times
        }

    return Forecast(start_time, mapping)


def specific_fixes(cubes):
    # Regrid any cubes not defined on the same grid as air_pressure (theta-levels,
    # centre of the C-grid). This should affect u, v, and density
    # Rename "height_above_reference_ellipsoid" to "altitude" as a lot of my code
    # currently assumes an altitude coordinate
    if 3 not in [cube.ndim for cube in cubes]:
        return

    regridded = []
    example_cube = cubes.extract_cube("upward_air_velocity")
    z = example_cube.coord("atmosphere_hybrid_height_coordinate")
    for cube in cubes:
        if cube.ndim == 3:
            cube.coord("height_above_reference_ellipsoid").rename("altitude")

            if cube.coord("atmosphere_hybrid_height_coordinate") != z:
                regridded.append(remap_3d(cube, example_cube))

    for cube in regridded:
        cubes.remove(cubes.extract_cube(cube.name()))
        cubes.append(cube)
