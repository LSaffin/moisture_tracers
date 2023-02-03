"""Top-level package for moisture_tracers."""

__author__ = """Leo Saffin"""
__email__ = "l.saffin@leeds.ac.uk"
__version__ = "0.1.0"


from math import floor
import datetime

import iris.exceptions
from dateutil.parser import parse as dateparse

import irise
from irise.interpolate import remap_3d
from irise.forecast import Forecast, _CubeLoader

from myscripts.projects.eurec4a.moisture_tracers import datadir, plotdir

# Filename Patterns
# model-variables_YYYYMMDDTHHMM_T+HH.nc and
# moisture-tracers_YYYYMMDDTHHMM_T+HH.nc
model_filename = "*_{start_time}_T+{lead_time:02d}.nc"
rmed_filename = "{start_time}Z_EUREC4A_ICfinal1km_{resolution}_{model_setup}_pver*{lead_time:03d}.pp"

# YYYYMMDDTHHMM_DomainResolution_T+HH_coarse_grid.nc
regridded_filename = "{start_time}_{resolution}_T+{lead_time:02d}_{grid}.nc"

start_times = ["20200123", "20200201", "20200204", "20200206", "20200208"]
resolutions = ["D100m_150m", "D100m_300m", "D100m_500m", "km1p1", "km2p2", "km4p4"]
grids = ["coarse_grid", "lagrangian_grid"]


def grey_zone_forecast(
    path=datadir + "regridded/",
    start_time="2020-02-01",
    resolution="km4p4",
    lead_times=range(1, 48 + 1),
    grid="coarse_grid",
    output_type="default",
    model_setup=None,
):
    """Return an irise.forecast.Forecast for an individual grey-zone simulation

    Args:
        path (str):
        start_time (datetime.datetime | str):
        resolution (str):
        lead_times (iterable): Sequence of lead times (in hours) in the requested
            simulation. Default is every hour from 1 to 48
        grid (str | None):
        output_type (str): Default or RMED. Default is my original output in netCDF
            files. RMED is for loading from .pp files that have used the "RMED
            toolbox" for output.
        model_setup (str): If using RMED files, the filenames also contain the model
            setup used (e.g. CoMorph or GAL8).

    Returns:
        irise.forecast.Forecast:
    """
    if isinstance(start_time, str):
        start_time = dateparse(start_time)

    start_time_str = start_time.strftime("%Y%m%dT%H%M")

    if output_type.lower() == "default":
        if grid is None:
            mapping = {
                start_time
                + datetime.timedelta(hours=dt): [
                    path
                    + model_filename.format(
                        start_time=start_time_str, lead_time=max(0, dt - 1)
                    ),
                ]
                for dt in lead_times
            }

        else:
            mapping = {
                start_time
                + datetime.timedelta(hours=dt): [
                    path
                    + regridded_filename.format(
                        start_time=start_time_str,
                        resolution=resolution,
                        lead_time=dt,
                        grid=grid,
                    ),
                ]
                for dt in lead_times
            }

    elif output_type.lower() == "rmed":
        if grid is None:
            mapping = {
                start_time + datetime.timedelta(hours=dt): [
                    path + resolution + "/" + rmed_filename.format(
                        start_time=start_time_str,
                        resolution=resolution,
                        model_setup=model_setup,
                        lead_time=12 * floor(dt/12),
                        grid=grid,
                    )
                ]
                for dt in lead_times
            }

            for dt in lead_times:
                if (dt % 12) == 0:
                    mapping[start_time + datetime.timedelta(hours=dt)].append(
                        path + resolution + "/" + rmed_filename.format(
                            start_time=start_time_str,
                            resolution=resolution,
                            model_setup=model_setup,
                            lead_time=dt - 12,
                            grid=grid,
                        )
                    )

    forecast = Forecast(start_time, mapping)
    forecast._loader = _ApproxLoader(forecast._loader.files)
    return forecast


def specific_fixes(cubes):
    # Regrid any cubes not defined on the same grid as air_pressure (theta-levels,
    # centre of the C-grid). This should affect u, v, and density
    # Rename "height_above_reference_ellipsoid" to "altitude" as a lot of my code
    # currently assumes an altitude coordinate
    regridded = []
    example_cube = cubes.extract_cube("upward_air_velocity")

    try:
        z = example_cube.coord("atmosphere_hybrid_height_coordinate")
        example_cube.coord("height_above_reference_ellipsoid").rename("altitude")
    except iris.exceptions.CoordinateNotFoundError:
        # Skip if we are not looking at height level data or
        # height_above_reference_ellipsoid has already been renamed
        return

    for cube in cubes:
        if cube.ndim == 3:
            try:
                cube.coord("height_above_reference_ellipsoid").rename("altitude")
            except iris.exceptions.CoordinateNotFoundError:
                pass

            if cube.coord("atmosphere_hybrid_height_coordinate") != z:
                regridded.append(remap_3d(cube, example_cube))

    for cube in regridded:
        cubes.remove(cubes.extract_cube(cube.name()))
        cubes.append(cube)


class _ApproxLoader(_CubeLoader):

    def _load_new_time(self, time):
        """ Loads a new cubelist and removes others if necessary

        Args:
            time (datetime.datetime): The new time to be loaded
        """
        # Clear space for the new files
        self._make_space(time)

        # Load data from files with that lead time
        cubes = irise.load(self.files[time])
        specific_fixes(cubes)

        # Add the data to the loaded files
        self._loaded[time] = cubes
