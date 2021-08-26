"""Top-level package for moisture_tracers."""

__author__ = """Leo Saffin"""
__email__ = 'l.saffin@leeds.ac.uk'
__version__ = '0.1.0'


import datetime

from irise.forecast import Forecast


def grey_zone_forecast(path, start_time, lead_times=range(24, 48+1)):
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

    mapping = {
        start_time + datetime.timedelta(hours=dt): [
            path + "model-variables_{}_T+{:02d}.nc".format(start_time_str, dt-1),
            path + "moisture-tracers_{}_T+{:02d}.nc".format(start_time_str, dt-1)
        ] for dt in lead_times
    }

    return Forecast(start_time, mapping)
