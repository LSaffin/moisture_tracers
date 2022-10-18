import numpy as np
import cartopy.crs as ccrs
import matplotlib.dates as mdates


date_format = mdates.DateFormatter("%HZ")

linestyles = dict(
    km1p1="-", km2p2="--", km4p4="-.", D100m_150m="-", D100m_300m="--", D100m_500m="-."
)
alphas = dict(
    km1p1=1.0, km2p2=1.0, km4p4=1.0, D100m_150m=0.5, D100m_300m=0.5, D100m_500m=0.5
)
labels = dict(
    D100m_150m="150 m",
    D100m_300m="300 m",
    D100m_500m="500 m",
    km1p1="1.1 km",
    km2p2="2.2 km",
    km4p4="4.4 km",
)
labels["150m"] = "150 m"
labels["300m"] = "300 m"
labels["500m"] = "500 m"
labels["1p1km"] = "1.1 km"
labels["2p2km"] = "2.2 km"
labels["4p4km"] = "4.4 km"

projection = ccrs.PlateCarree()

lw_flux_plot_kwargs = dict(vmin=260, vmax=300, cmap="cmc.grayC")
satellite_plot_kwargs = dict(vmin=280, vmax=300, cmap="cmc.nuuk_r")
