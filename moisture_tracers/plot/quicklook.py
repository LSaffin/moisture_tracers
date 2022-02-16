"""

Usage:
    quicklook.py <path> <start_time> [<resolution>] [<grid>] [<output_path>]
    quicklook.py (-h | --help)

Arguments:
    <path>
    <start_time>
    <resolution>
    <grid>
    <output_path>

Options:
    -h --help
        Show this screen.
"""

import matplotlib.pyplot as plt
import matplotlib.colors as colors

from twinotter.external import eurec4a
from twinotter.util.scripting import parse_docopt_arguments
import irise
from irise import plot

from moisture_tracers import grey_zone_forecast


zlevs = ("altitude", [50, 300, 500, 1000, 1500, 2000, 3000, 4000])


def main(path, start_time, resolution=None, grid=None, output_path="."):
    forecast = grey_zone_forecast(
        path, start_time=start_time, resolution=resolution, grid=grid
    )
    generate(forecast, output_path=output_path)


def generate(forecast, output_path="."):
    """

    Args:
        forecast (irise.forecast.Forecast):

    Returns:

    """
    for cubes in forecast:
        specific_fixes(cubes)

        make_plots(cubes, forecast.lead_time, output_path=output_path)


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


def make_plots(cubes, lead_time, output_path="."):
    print(lead_time)

    for name, levels, function, args, kwargs in [
        (
            "surface_air_pressure",
            None,
            plot.contour,
            [range(99500, 102000, 10)],
            dict(colors="k"),
        ),
        (
            "atmosphere_boundary_layer_thickness",
            None,
            plot.pcolormesh,
            [],
            dict(vmin=0, vmax=1500, cmap="cividis"),
        ),
        (
            "toa_outgoing_shortwave_flux",
            None,
            plot.pcolormesh,
            [],
            dict(vmin=0, vmax=2000, cmap="Greys_r"),
        ),
        (
            "surface_downwelling_shortwave_flux_in_air",
            None,
            plot.pcolormesh,
            [],
            dict(vmin=0, vmax=1000, cmap="Greys"),
        ),
        (
            "toa_outgoing_longwave_flux",
            None,
            plot.pcolormesh,
            [],
            dict(vmin=200, vmax=300, cmap="Greys"),
        ),
        (
            "surface_downwelling_longwave_flux_in_air",
            None,
            plot.pcolormesh,
            [],
            dict(vmin=350, vmax=450, cmap="Greys_r"),
        ),
        (
            "surface_upward_sensible_heat_flux",
            None,
            plot.pcolormesh,
            [],
            dict(vmin=0, vmax=100, cmap="cividis"),
        ),
        (
            "surface_upward_latent_heat_flux",
            None,
            plot.pcolormesh,
            [],
            dict(vmin=0, vmax=300, cmap="cividis"),
        ),
        (
            "boundary_layer_type",
            None,
            plot.pcolormesh,
            [],
            dict(vmin=-0.5, vmax=9.5, cmap="tab10"),
        ),
        (
            "total_column_water",
            None,
            plot.pcolormesh,
            [],
            dict(vmin=0, vmax=40, cmap="Blues"),
        ),
        (
            "atmosphere_cloud_liquid_water_content",
            None,
            plot.pcolormesh,
            [],
            dict(vmin=0, vmax=1, cmap="Blues"),
        ),
        (
            "stratiform_rainfall_amount",
            None,
            plot.pcolormesh,
            [],
            dict(vmin=0, cmap="Blues"),
        ),
        (
            "cloud_thickness",
            None,
            plot.pcolormesh,
            [],
            dict(vmin=500, vmax=3000, cmap="cubehelix_r"),
        ),
        (
            "cloud_top_height",
            None,
            plot.pcolormesh,
            [],
            dict(vmin=500, vmax=3000, cmap="cubehelix_r"),
        ),
        (
            "upward_air_velocity",
            zlevs,
            plot.pcolormesh,
            [],
            dict(vmin=-1, vmax=1, cmap="Spectral"),
        ),
        ("air_potential_temperature", zlevs, plot.pcolormesh, [], dict(cmap="inferno")),
        (
            "equivalent_potential_temperature",
            zlevs,
            plot.pcolormesh,
            [],
            dict(cmap="inferno"),
        ),
        (
            "specific_humidity",
            zlevs,
            plot.pcolormesh,
            [],
            dict(vmin=0, vmax=0.02, cmap="cubehelix_r"),
        ),
        ("relative_humidity", zlevs, plot.pcolormesh, [], dict(cmap="cubehelix_r")),
        (
            "rain_mixing_ratio",
            zlevs,
            plot.pcolormesh,
            [],
            dict(norm=colors.LogNorm(vmin=1e-10, vmax=1e-4), cmap="cubehelix_r"),
        ),
        (
            "mass_fraction_of_cloud_liquid_water_in_air",
            zlevs,
            plot.pcolormesh,
            [],
            dict(norm=colors.LogNorm(vmin=1e-10, vmax=1e-4), cmap="cubehelix_r"),
        ),
        (
            "advection_only_q",
            zlevs,
            plot.pcolormesh,
            [],
            dict(vmin=0, vmax=0.02, cmap="cubehelix_r"),
        ),
        (
            "total_minus_advection_only_q",
            zlevs,
            plot.pcolormesh,
            [],
            dict(vmin=-0.01, vmax=0.01, cmap="seismic_r"),
        ),
        (
            "microphysics_q",
            zlevs,
            plot.pcolormesh,
            [],
            dict(vmin=-0.01, vmax=0.01, cmap="seismic_r"),
        ),
        (
            "microphysics_cloud_q",
            zlevs,
            plot.pcolormesh,
            [],
            dict(vmin=-0.01, vmax=0.01, cmap="seismic_r"),
        ),
        (
            "boundary_layer_q",
            zlevs,
            plot.pcolormesh,
            [],
            dict(vmin=-0.01, vmax=0.01, cmap="seismic_r"),
        ),
        (
            "boundary_layer_cloud_q",
            zlevs,
            plot.pcolormesh,
            [],
            dict(vmin=-0.01, vmax=0.01, cmap="seismic_r"),
        ),
        (
            "cloud_q",
            zlevs,
            plot.pcolormesh,
            [],
            dict(vmin=-0.001, vmax=0.001, cmap="seismic_r"),
        ),
        (
            "leonard_terms_q",
            zlevs,
            plot.pcolormesh,
            [],
            dict(vmin=-0.001, vmax=0.001, cmap="seismic_r"),
        ),
    ]:
        try:
            cube = irise.convert.calc(name, cubes, levels=levels)
            print(name)

            fig, axes = plt.subplots(figsize=(5, 8))
            if levels is None:
                function(cube, *args, **kwargs)
                eurec4a.add_halo_circle(ax=plt.gca())

                fig.savefig(
                    output_path
                    + "/{}_T+{}.png".format(
                        name,
                        int(lead_time.total_seconds() // 3600),
                    )
                )

            else:
                for n in range(len(levels[1])):
                    function(cube[n], *args, **kwargs)
                    eurec4a.add_halo_circle(ax=plt.gca())

                    fig.savefig(
                        output_path
                        + "/{}_{}{}_T+{}.png".format(
                            name,
                            levels[0],
                            levels[1][n],
                            int(lead_time.total_seconds() // 3600),
                        )
                    )
                    plt.clf()
        except ValueError:
            print("{} not in cubelist at this time".format(name))

        plt.close(fig)


if __name__ == "__main__":
    parse_docopt_arguments(main, __doc__)
