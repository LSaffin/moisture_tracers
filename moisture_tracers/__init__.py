"""Top-level package for moisture_tracers."""

__author__ = """Leo Saffin"""
__email__ = 'l.saffin@leeds.ac.uk'
__version__ = '0.1.0'


import datetime

from irise.forecast import Forecast


# Filename Patterns
# model-variables_YYYYMMDDTHHMM_T+HH.nc and
# moisture-tracers_YYYYMMDDTHHMM_T+HH.nc
model_filename = "*_{start_time}_T+{lead_time:02d}.nc"

# YYYYMMDDTHHMM_DomainResolution_T+HH_coarse_grid.nc
regridded_filename = "{start_time}_{resolution}_T+{lead_time:02d}_{grid}.nc"


def grey_zone_forecast(
        path,
        start_time,
        resolution="km4p4",
        lead_times=range(24, 48+1),
        grid=None,
):
    """Return an irise.forecast.Forecast for an individual grey-zone simulation

    Args:
        path (str):
        start_time (datetime.datetime):
        lead_times (iterable): Sequence of lead times (in hours) in the requested
            simulation. Default is every hour from 1 to 48

    Returns:
        irise.forecast.Forecast:
    """
    start_time_str = start_time.strftime("%Y%m%dT%H%M")

    if grid is None:
        mapping = {
            start_time + datetime.timedelta(hours=dt): [
                path + model_filename.format(
                    start_time=start_time_str,
                    lead_time=dt-1
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
