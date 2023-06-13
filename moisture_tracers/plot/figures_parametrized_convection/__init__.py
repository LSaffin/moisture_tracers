from moisture_tracers import plotdir, datadir, grey_zone_forecast

plotdir = plotdir + "parametrized_convection/"

forecasts = []
for resolution in ["km1p1", "km4p4"]:
    forecasts.append(grey_zone_forecast(
        path=datadir + "regridded_vn12/",
        start_time="2020-02-01",
        resolution=resolution,
        lead_times=range(1, 48+1),
        grid="lagrangian_grid",
    ))

for model_setup in ["CoMorphA", "GAL8"]:
    for resolution in ["km4p4", "km10"]:
        forecasts.append(grey_zone_forecast(
            path=datadir + "regridded_conv/",
            start_time="2020-02-01",
            resolution=f"{model_setup}_{resolution}",
            lead_times=range(3, 48+1, 3),
            grid="lagrangian_grid",
        ))
