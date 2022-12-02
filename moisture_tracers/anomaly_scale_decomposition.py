"""
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import generic_filter
import iris.quickplot as qplt
from iris.analysis import MEAN, AreaWeighted, Nearest

from irise import convert

from moisture_tracers import grey_zone_forecast, datadir
from moisture_tracers.regrid_common import generate_1km_grid


def main():
    start_time = "2020-02-01"
    path = datadir + "regridded/"
    grid = "coarse_grid"
    lead_time = 40

    resolution = "D100m_150m"
    forecast = grey_zone_forecast(
        path, start_time=start_time, resolution=resolution, grid=grid
    )

    cubes = forecast.set_lead_time(hours=lead_time)
    qt = convert.calc("total_column_water", cubes)

    qt_mean, qt_16km, qt_cu = decompose_scales(qt, coarse_factor=4)
    fig, axes = plt.subplots(1, 3, figsize=(16, 8))

    plt.axes(axes[0])
    qplt.pcolormesh(qt)
    plt.title(r"$q_t$")

    plt.axes(axes[1])
    qplt.pcolormesh(qt_16km, vmin=-4, vmax=4, cmap="seismic")
    plt.title(r"$q_t^{\prime\prime}$")

    plt.axes(axes[2])
    qplt.pcolormesh(qt_cu, vmin=-4, vmax=4, cmap="seismic")
    plt.title(r"$q_t^{\prime\prime\prime}$")

    plt.show()


def decompose_scales(cube, coarse_factor=4, large_scale_factor=None):
    coarse_grid = generate_1km_grid(cube, coarse_factor=coarse_factor)

    # Average the full field to the mesoscale
    cube_mesoscale = cube.regrid(coarse_grid, AreaWeighted())
    # TODO: Only use the full grid that is used in the coarse graining
    # i.e. chop off ends that aren't divisible by coarse-graining factor
    pass

    # Small-scale anomalies
    cube_mesoscale_full_grid = cube_mesoscale.regrid(cube, Nearest())
    cube_small_scale = cube - cube_mesoscale_full_grid

    if large_scale_factor is None:
        # Large Scale is domain mean
        cube_large_scale = cube.collapsed(["grid_longitude", "grid_latitude"], MEAN)
    else:
        # Large scale is median filtered field
        filter_large = np.ones(cube.ndim, dtype=int)
        for coord in ["grid_longitude", "grid_latitude"]:
            n = cube.coord_dims(coord)
            filter_large[n] = large_scale_factor

        large_scale = generic_filter(
            cube_mesoscale.data, function=np.median, size=filter_large
        )
        cube_large_scale = cube_mesoscale.copy(data=large_scale)

    # Subtract large scale to get mesoscale anomalies
    cube_mesoscale = cube_mesoscale - cube_large_scale

    return cube_large_scale, cube_mesoscale, cube_small_scale


if __name__ == "__main__":
    main()
