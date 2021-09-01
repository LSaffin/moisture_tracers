import matplotlib.pyplot as plt

import iris.plot as iplt

colours = plt.rcParams['axes.prop_cycle'].by_key()['color']


def identify_possibles(forecast):
    """Plot and label cold-pool contours at each timestep
    """
    for n, cubes in enumerate(forecast):
        evaporation_tracer = cubes.extract_cube("microphysics_evaporation_q")
        contours = get_cold_pool_contours(evaporation_tracer)

        for m, contour in enumerate(contours):
            # Resulting contour is 180 off the actual data coordinates. No idea why
            plt.plot(contour[:, 0] - 180, contour[:, 1], color=colours[m])
            plt.text(contour[0, 0] - 180, contour[0, 1], str(m), color=colours[m])

        plt.savefig("cold_pools_T+{:02d}.png".format(n))
        plt.close()


def get_cold_pool_contours(evaporation_tracer, threshold=1e-4):
    cs = iplt.contour(evaporation_tracer, [threshold])

    return cs.allsegs[0]
