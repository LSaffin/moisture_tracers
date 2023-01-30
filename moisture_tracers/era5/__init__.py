import datetime

from dateutil.parser import parse as dateparse
from irise.forecast import Forecast

from moisture_tracers import datadir

datadir = datadir + "era5/"


def era5_as_forecast(start_time="2020-02-01", lead_times=range(48 + 1), path=datadir):
    """Return an irise.forecast.Forecast for ERA5 data

    Args:
        start_time (datetime.datetime | str):
        lead_times (iterable): Sequence of lead times (in hours) in the requested
            simulation. Default is every hour from 1 to 48
        path (str):

    Returns:
        irise.forecast.Forecast:
    """
    if isinstance(start_time, str):
        start_time = dateparse(start_time)

    mapping = {}
    for n in lead_times:
        time = start_time + datetime.timedelta(hours=n)
        mapping[time] = [
            path + "era5_{}_single_levels.nc".format(time.strftime("%Y%m%dT%H%M")),
            path + "era5_{}_pressure_levels.nc".format(time.strftime("%Y%m%dT%H%M")),
        ]

    return Forecast(start_time, mapping)
