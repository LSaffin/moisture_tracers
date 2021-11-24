import warnings

from dateutil.parser import parse as dateparse
import numpy as np

from pylagranto import caltra

from moisture_tracers import grey_zone_forecast, datadir


def main():
    start_time = dateparse("2020-02-01")

    path = datadir + "regridded/"
    resolution = "km1p1"
    grid = "coarse_grid"

    x0 = 302.5
    y0 = 13.5
    z0 = 500
    levels = ("height_above_reference_ellipsoid", [z0])

    forecast = grey_zone_forecast(path, start_time, resolution=resolution, grid=grid)
    trainp = np.array([[x0, y0, z0]])

    traout = caltra.caltra(trainp, forecast._loader.files, fbflag=-1, levels=levels)

    traout.save(
        "trajectories_{}_{}_{}m.pkl".format(
            start_time.strftime("%Y%m%d"), resolution, z0
        )
    )


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()
