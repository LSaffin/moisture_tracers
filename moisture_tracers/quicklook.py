"""

Usage:
    quicklook.py <path> <year> <month> <day> [<resolution>] [<grid>]
    quicklook.py (-h | --help)

Arguments:
    <path>
    <year>
    <month>
    <day>
    <resolution>
    <grid>

Options:
    -h --help
        Show this screen.
"""
import datetime

import matplotlib.pyplot as plt

from twinotter.external import eurec4a
from twinotter.util.scripting import parse_docopt_arguments
import irise
from irise import plot

from . import grey_zone_forecast


zlevs = ("altitude", [50, 300, 500, 1000, 1500, 2000, 3000, 4000])


def main(path, year, month, day, resolution=None, grid=None):

    start_time = datetime.datetime(
        year=int(year),
        month=int(month),
        day=int(day),
    )
    forecast = grey_zone_forecast(
        path, start_time=start_time, resolution=resolution, grid=grid
    )
    generate(forecast, )


def generate(forecast):
    """

    Args:
        forecast (irise.forecast.Forecast):

    Returns:

    """
    for cubes in forecast:
        specific_fixes(cubes)

        make_plots(cubes, forecast.lead_time)


def specific_fixes(cubes):
    # Regrid any cubes not defined on the same grid as air_pressure (theta-levels,
    # centre of the C-grid). This should affect u, v, and density
    # Rename "height_above_reference_ellipsoid" to "altitude" as a lot of my code
    # currently assumes an altitude coordinate

    regridded = []
    example_cube = cubes.extract_cube("air_pressure")
    z = example_cube.coord("atmosphere_hybrid_height_coordinate")
    for cube in cubes:
        if cube.ndim == 3:
            cube.coord("height_above_reference_ellipsoid").rename("altitude")

            if cube.coord("atmosphere_hybrid_height_coordinate") != z:
                regridded.append(irise.interpolate.remap_3d(cube, example_cube))

    for cube in regridded:
        cubes.remove(cubes.extract_cube(cube.name()))
        cubes.append(cube)


def make_plots(cubes, lead_time):
    print(lead_time)

    for name, levels, function, args, kwargs in [
        ("surface_air_pressure", None, plot.contour, [range(95000, 105000, 50)], dict(colors="k")),
        ("atmosphere_boundary_layer_thickness", None, plot.pcolormesh, [], dict(vmin=0, vmax=2000, cmap="cividis")),
        ("toa_outgoing_shortwave_flux", None, plot.pcolormesh, [], dict(vmin=0, vmax=2000, cmap="Greys_r")),
        ("surface_downwelling_shortwave_flux_in_air", None, plot.pcolormesh, [], dict(vmin=0, vmax=2000, cmap="Greys")),
        ("toa_outgoing_longwave_flux", None, plot.pcolormesh, [], dict(vmin=0, vmax=300, cmap="Greys")),
        ("surface_downwelling_longwave_flux_in_air", None, plot.pcolormesh, [], dict(vmin=0, vmax=500, cmap="Greys")),
        ("surface_upward_sensible_heat_flux", None, plot.pcolormesh, [], dict(vmin=0, vmax=200, cmap="cividis")),
        ("surface_upward_latent_heat_flux", None, plot.pcolormesh, [], dict(vmin=0, vmax=500, cmap="cividis")),
        ("COMBINED BOUNDARY LAYER TYPE", None, plot.pcolormesh, [], dict(vmin=-0.5, vmax=9.5, cmap="tab10")),
        ("total_column_water", None, plot.pcolormesh, [], dict(vmin=0, cmap="Blues")),
        ("total_column_liquid_water", None, plot.pcolormesh, [], dict(vmin=0, cmap="Blues")),

        ("upward_air_velocity", zlevs, plot.pcolormesh, [], dict(vmin=-2, vmax=2, cmap="Spectral")),
        ("air_potential_temperature", zlevs, plot.pcolormesh, [], dict(cmap="inferno")),
        ("equivalent_potential_temperature", zlevs, plot.pcolormesh, [], dict(cmap="inferno")),
        ("specific_humidity", zlevs, plot.pcolormesh, [], dict(vmin=0, vmax=0.02, cmap="Spectral")),
        ("advection_only_q", zlevs, plot.pcolormesh, [], dict(vmin=0, vmax=0.02, cmap="seismic_r")),
        ("total_minus_advection_only_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        ("microphysics_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        ("microphysics_settling_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        ("microphysics_fixes_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        #("microphysics_deposition_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        ("microphysics_evaporation_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        #("microphysics_melting_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        ("boundary_layer_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        ("boundary_layer_entrainment_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        ("boundary_layer_surface_fluxes_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        ("boundary_layer_other_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        ("theta_perturbations_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        ("leonard_terms_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        ("advection_correction_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
        ("solver_q", zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")),
    ]:
        print(name)
        cube = irise.convert.calc(name, cubes, levels=levels)

        fig, axes = plt.subplots(figsize=(5, 8))
        if levels is None:
            function(cube, *args, **kwargs)
            eurec4a.add_halo_circle(ax=plt.gca())

            fig.savefig("{}_T+{}.png".format(
                name,
                int(lead_time.total_seconds() // 3600),
            ))

        else:
            for n in range(len(levels[1])):
                function(cube[n], *args, **kwargs)
                eurec4a.add_halo_circle(ax=plt.gca())

                fig.savefig("{}_{}{}_T+{}.png".format(
                    name,
                    levels[0],
                    levels[1][n],
                    int(lead_time.total_seconds() // 3600),
                ))
                plt.clf()

        plt.close(fig)


if __name__ == '__main__':
    parse_docopt_arguments(main, __doc__)
