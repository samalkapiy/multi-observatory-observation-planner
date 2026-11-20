import astropy.units as u
from astropy.coordinates import (
    AltAz,
    EarthLocation,
    SkyCoord,
    get_body,
    get_sun,
)
from astropy.time import Time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def calculate_times(
    start_time,
    duration_hours,
    cadence_minutes
):
    # Create observation timestamps
    start = Time(start_time, scale="utc")

    n_samples = int(duration_hours * 60 / cadence_minutes) + 1

    times = start + (
        np.arange(n_samples) * cadence_minutes * u.min
    )
    return times


def altitude_KP(ra_deg=20,dec_deg=10,longitude_deg=111,latitude_deg=31,elevation_m=0):
    # Observatory location
    location = EarthLocation.from_geodetic(
        lon=longitude_deg * u.deg,
        lat=latitude_deg * u.deg,
        height=elevation_m * u.m,
    )

    times = calculate_times(    
        start_time="2026-11-05T00:00:00",
        duration_hours=12,
        cadence_minutes=10)
    
    # Coordinate frame
    frame = AltAz(
        obstime=times,
        location=location,
    )
    # Target coordinates
    target = SkyCoord(
        ra=ra_deg * u.deg,
        dec=dec_deg * u.deg,
        frame="icrs",
    )
    target_altitude = target.transform_to(frame).alt.deg

    # Sun altitude
    sun_altitude = get_sun(times).transform_to(frame).alt.deg

    # Moon altitude (topocentric)
    moon_altitude = get_body(
        "moon",
        times,
        location=location,
    ).transform_to(frame).alt.deg

    return pd.DataFrame({
        "Time (UTC)": times.utc.to_datetime(),
        "Target": target_altitude,
        "Sun": sun_altitude,
        "Moon": moon_altitude,
    })


df = altitude_KP()

print(df.head())

plt.plot(df['Time (UTC)'], df['Target'], label='Target')
plt.plot(df['Time (UTC)'], df['Sun'], label='Sun')
plt.plot(df['Time (UTC)'], df['Moon'], label='Moon')
plt.show()