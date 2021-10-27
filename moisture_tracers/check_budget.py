"""
Plot maps of the moisture tracer budget on all vertical levels

Usage:
    check_budget.py <filename>
    check_budget.py (-h | --help)

Arguments:
    <filename>
Options:
    -h --help
        Show help
"""

from tqdm import tqdm
import matplotlib.pyplot as plt
import iris.plot as iplt

import irise
from irise import convert
from twinotter.util.scripting import parse_docopt_arguments

from myscripts import plotdir


def main(filename):
    tracers = irise.load(filename)

    for k in tqdm(range(40)):
        check_budget(
            tracers,
            "total_minus_advection_only_q",
            ["microphysics_q",
             "boundary_layer_q",
             "theta_perturbations_q",
             "leonard_terms_q",
             "advection_correction_q",
             "solver_q",
             ],
            ncols=3,
            k=k,
            vmin=-1e-2,
            vmax=1e-2,
            cmap="seismic_r"
        )
        plt.savefig(plotdir + "q_budget_k{}.png".format(k))
        plt.close()


def check_budget(cubes, full, subsets, ncols=4, k=0, **kwargs):
    """

    Args:
        cubes (iris.cube.CubeList): The cube list to calculate variables from
        full (str): The name of the field containing the total budget
        subsets (list): The names of components that should add up to the full field
        ncols (int): Number of columns for the plot
        k (int): Vertical level index to plot
        **kwargs: Keyword arguments for iplt.pcolormesh

    Returns:

    """
    nfigs = 2 + len(subsets)
    nrows = (nfigs + 1) // ncols

    full = convert.calc(full, cubes)
    subsets = convert.calc(subsets, cubes)

    fig, axes = plt.subplots(nrows, ncols, figsize=(16, nrows * 5))

    # Plot the full field
    plt.axes(axes[0, 0])
    iplt.pcolormesh(full[k], **kwargs)
    plt.title(full.name())

    # Plot the sum of the individual subsets
    subset_total = sum(subsets)
    plt.axes(axes[1 // ncols, 1 % ncols])
    iplt.pcolormesh(subset_total[k], **kwargs)
    plt.title("Sum of subsets")

    # Plot the residual
    plt.axes(axes[2 // ncols, 2 % ncols])
    im = iplt.pcolormesh((full - subset_total)[k], **kwargs)
    plt.title("Residual")

    # Plot the individual subsets
    for i, cube in enumerate(subsets):
        plt.axes(axes[(i + 3) // ncols, (i + 3) % ncols])
        iplt.pcolormesh(cube[k], **kwargs)
        plt.title(cube.name())

    plt.subplots_adjust(bottom=0.2)
    cax = plt.axes([0.1, 0.1, 0.8, 0.05])
    fig.colorbar(im, cax=cax, orientation="horizontal")


if __name__ == "__main__":
    parse_docopt_arguments(main, __doc__)
