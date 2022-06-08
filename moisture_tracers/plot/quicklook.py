"""

Usage:
    quicklook.py <path> <start_time> <resolution> <grid> [<output_path>] [--replace_existing]
    quicklook.py (-h | --help)

Arguments:
    <path>
    <start_time>
    <resolution>
    <grid>
    <output_path>
    <replace_existing>

Options:
    -h --help
        Show this screen.
"""
import pathlib

from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib.colors as colors

from twinotter.external import eurec4a
from twinotter.util.scripting import parse_docopt_arguments
import irise
from irise import plot

from moisture_tracers import grey_zone_forecast, specific_fixes


zlevs = ("altitude", [50, 300, 500, 1000, 1500, 2000, 3000, 4000])
diagnostics = dict(
    surface_air_pressure=[None, plot.contour, [range(99500, 102000, 10)], dict(colors="k")],
    atmosphere_boundary_layer_thickness=[None, plot.pcolormesh, [], dict(vmin=0, vmax=1500, cmap="cividis")],
    toa_outgoing_shortwave_flux=[None, plot.pcolormesh, [], dict(vmin=0, vmax=2000, cmap="Greys_r")],
    surface_downwelling_shortwave_flux_in_air=[None, plot.pcolormesh, [], dict(vmin=0, vmax=1000, cmap="Greys")],
    toa_outgoing_longwave_flux=[None, plot.pcolormesh, [], dict(vmin=200, vmax=300, cmap="Greys")],
    surface_downwelling_longwave_flux_in_air=[None, plot.pcolormesh, [], dict(vmin=350, vmax=450, cmap="Greys_r")],
    surface_upward_sensible_heat_flux=[None, plot.pcolormesh, [], dict(vmin=0, vmax=100, cmap="cividis")],
    surface_upward_latent_heat_flux=[None, plot.pcolormesh, [], dict(vmin=0, vmax=300, cmap="cividis")],
    boundary_layer_type=[None, plot.pcolormesh, [], dict(vmin=-0.5, vmax=9.5, cmap="tab10")],
    total_column_water=[None, plot.pcolormesh, [], dict(vmin=0, vmax=40, cmap="Blues")],
    atmosphere_cloud_liquid_water_content=[None, plot.pcolormesh, [], dict(vmin=0, vmax=1, cmap="Blues")],
    stratiform_rainfall_amount=[None, plot.pcolormesh, [], dict(vmin=0, cmap="Blues")],
    cloud_thickness=[None,  plot.pcolormesh, [], dict(vmin=500, vmax=3000, cmap="cubehelix_r")],
    cloud_top_height=[None, plot.pcolormesh, [], dict(vmin=500, vmax=3000, cmap="cubehelix_r")],

    upward_air_velocity=[zlevs, plot.pcolormesh, [], dict(vmin=-1, vmax=1, cmap="Spectral")],
    air_potential_temperature=[zlevs, plot.pcolormesh, [], dict(cmap="inferno")],
    equivalent_potential_temperature=[zlevs, plot.pcolormesh, [], dict(cmap="inferno")],
    specific_humidity=[zlevs, plot.pcolormesh, [], dict(vmin=0, vmax=0.02, cmap="cubehelix_r")],
    relative_humidity=[zlevs, plot.pcolormesh, [], dict(cmap="cubehelix_r")],
    rain_mixing_ratio=[zlevs, plot.pcolormesh, [], dict(norm=colors.LogNorm(vmin=1e-10, vmax=1e-4), cmap="cubehelix_r")],
    mass_fraction_of_cloud_liquid_water_in_air=[zlevs, plot.pcolormesh, [], dict(norm=colors.LogNorm(vmin=1e-10, vmax=1e-4), cmap="cubehelix_r")],
    advection_only_q=[zlevs, plot.pcolormesh, [], dict(vmin=0, vmax=0.02, cmap="cubehelix_r")],
    total_minus_advection_only_q=[zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")],
    microphysics_q=[zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")],
    microphysics_cloud_q=[zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")],
    boundary_layer_q=[zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")],
    boundary_layer_cloud_q=[zlevs, plot.pcolormesh, [], dict(vmin=-0.01, vmax=0.01, cmap="seismic_r")],
    cloud_q=[zlevs, plot.pcolormesh, [], dict(vmin=-0.001, vmax=0.001, cmap="seismic_r")],
    leonard_terms_q=[zlevs, plot.pcolormesh, [], dict(vmin=-0.001, vmax=0.001, cmap="seismic_r")],
)


def get_wind_shear(cubes):
    u = irise.convert.calc("x_wind", cubes, levels=("air_pressure", [70000, 100000]))
    v = irise.convert.calc("y_wind", cubes, levels=("air_pressure", [70000, 100000]))

    du_dz = u[1] - u[0]
    dv_dz = v[1] - v[0]

    return (du_dz ** 2 + dv_dz ** 2) ** 0.5


def get_lts(cubes):
    theta = irise.convert.calc(
        "air_potential_temperature", cubes, levels=("air_pressure", [70000, 100000])
    )

    return theta[1] - theta[0]


diagnostics["wind_shear"] = [
    get_wind_shear,
    plot.pcolormesh,
    [],
    dict(vmin=0, vmax=10, cmap="cubehelix_r"),
]
diagnostics["lower_tropospheric_stability"] = [
    get_lts,
    plot.pcolormesh,
    [],
    dict(vmin=-30, vmax=-15, cmap="cubehelix"),
]


def main(
    path,
    start_time,
    resolution=None,
    grid=None,
    output_path="./",
    replace_existing=False,
):
    forecast = grey_zone_forecast(
        path, start_time=start_time, resolution=resolution, grid=grid
    )

    for cubes in forecast:
        specific_fixes(cubes)
        make_plots(
            cubes,
            forecast.lead_time,
            output_path=output_path,
            replace_existing=replace_existing,
        )


def make_plots(cubes, lead_time, output_path="./", replace_existing=False):
    print(lead_time)
    lead_time = str(int(lead_time.total_seconds() // 3600)).zfill(2)

    for name in tqdm(diagnostics):
        levels, function, args, kwargs = diagnostics[name]
        if levels is None:
            fname = pathlib.Path(output_path + "/{}_T+{}.png".format(name, lead_time))
            if replace_existing or not fname.exists():
                try:
                    cube = irise.convert.calc(name, cubes)
                    function(cube, *args, **kwargs)
                    eurec4a.add_halo_circle(ax=plt.gca())
                    plt.savefig(fname)
                    plt.close()
                except ValueError:
                    print("{} not in cubelist at this time".format(name))

        elif callable(levels):
            fname = pathlib.Path(output_path + "/{}_T+{}.png".format(name, lead_time))
            if replace_existing or not fname.exists():
                try:
                    cube = levels(cubes)
                    function(cube, *args, **kwargs)
                    eurec4a.add_halo_circle(ax=plt.gca())
                    plt.savefig(fname)
                    plt.close()
                except ValueError:
                    print("{} not in cubelist at this time".format(name))

        else:
            fnames = [
                pathlib.Path(
                    output_path
                    + "{}_{}{}_T+{}.png".format(name, levels[0], level, lead_time)
                )
                for level in levels[1]
            ]

            if replace_existing:
                levels_to_plot = levels[1]
            else:
                levels_to_plot = [
                    levels[1][n] for n, path in enumerate(fnames) if not path.exists()
                ]
                fnames = [
                    fnames[n] for n, path in enumerate(fnames) if not path.exists()
                ]

            if len(levels_to_plot) > 0:
                try:
                    cube = irise.convert.calc(
                        name, cubes, levels=(levels[0], levels_to_plot)
                    )
                    for n in range(len(levels_to_plot)):
                        function(cube[n], *args, **kwargs)
                        eurec4a.add_halo_circle(ax=plt.gca())
                        plt.savefig(fnames[n])
                        plt.close()
                except ValueError:
                    print("{} not in cubelist at this time".format(name))


if __name__ == "__main__":
    parse_docopt_arguments(main, __doc__)
