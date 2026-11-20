"""Visibility calculations for ground-based observatories."""
from datetime import timedelta

import astropy.units as u
import numpy as np
from astropy.coordinates import AltAz, SkyCoord, get_sun, get_body
from astropy.time import Time
from astropy.utils import iers

from .observatories import OBSERVATORIES    #from observotories.py import the OBSERVATORIES dictionary

# Avoid an implicit network download of Earth-orientation data.
#iers: International Earth Rotation and Reference Systems Service.
iers.conf.auto_download = False                                         # set to false to avoid auto download. in case of network issues, the code will not fail. 
iers.conf.iers_degraded_accuracy = "warn"                               #give a warning if the data is not accurate. This is important for astronomical calculations that require precise timing and positioning, such as tracking celestial objects or predicting eclipses.


# Here we need to find the visibility windows of the target. Imagine if we are evaluating the target's visibility every 10 mins
# we will have a boolean array of True and False values. True means the target is visible at that time, False means it is not visible.
def _find_windows(times, visible):
    """Convert a boolean time grid into contiguous UTC visibility windows."""
    windows = []                                                        #initializing the variables windows and start. 
    start = None                                                        #keeps track of the index where a visibility window begins. Initially this is none because we havn't found a visibility window yet. 

    for index, is_visible in enumerate(visible):                        # iterates through the boolean array of visibility. index is the current index of the array. 
        if is_visible and start is None:                                #This checks two conditions: 1. The target is visible (is_visible = True). 2. We haven't already started recording a visibility window.
            start = index                                               # give the index of the first True value in the array 'visible'

        is_last = index == len(visible) - 1                             #is_last is a boolean value (False, true). Checks if index == len(visible)-1.
        if start is not None and (not is_visible or is_last):           # Checks the conditions, have we already started a visibility window? Has the target become invisible OR have we reached the final sample?
            end = index if is_visible and is_last else index - 1        #calculating the ending index
            windows.append({                                            #adds a dictionary to the windows list.
                "start_utc": times[start].isot,                         #Retrieves the time at which the visibility window begins .isot converts the Astropy Time object into an ISO-formatted timestamp.
                "end_utc": times[end].isot,
                "sample_count": end - start + 1,                        # add 1 because index started from zero. Have to accout for that.
            })
            start = None                                                #have to reset the start variable to None so that we can find the next visibility window in the next iterations of the loop.

    return windows                                                      #function returns a list of visibility windows.

# eg: visible = [False, True, True, True, False]. The loop detects the end at index 4. But index 4 is not visible. So last index = 4-1 (index - 1)=3
# but if visible = [False, True, True, True, True]. The loop detects the end at index 4. But index 4 is visible. So last index = 4 (index)



def plan_observations(
    ra_deg: float,
    dec_deg: float,
    start_time: str,
    duration_hours: float = 12.0,
    cadence_minutes: int = 10,                                                  # visibility evaluated at every 10 mins. This is the cadence of the observation. The planner will check the visibility of the target every 10 mins.
    min_altitude_deg: float = 25.0,
    require_astronomical_darkness: bool = True,
):
    """Evaluate a fixed celestial target against ground-site constraints.

    A sample is considered visible when the target is above the requested
    altitude. If darkness is required, the Sun must also be below -18 deg.
    This is a planning aid, not a substitute for observatory constraints.
    """
    #validating input parameters.
    if not -90 <= dec_deg <= 90:
        raise ValueError("dec_deg must be between -90 and +90 degrees")
    if not 0 <= ra_deg < 360:
        raise ValueError("ra_deg must be in [0, 360) degrees")
    if duration_hours <= 0 or duration_hours > 72:
        raise ValueError("duration_hours must be > 0 and <= 72")
    if cadence_minutes <= 0 or cadence_minutes > 60:
        raise ValueError("cadence_minutes must be between 1 and 60")
    if not 0 <= min_altitude_deg <= 90:
        raise ValueError("min_altitude_deg must be between 0 and 90")

    start = Time(start_time, scale="utc")                                       #creating an astropy Time object
    n_samples = int(duration_hours * 60 / cadence_minutes) + 1                  #creating an observation time grid. adding 1 to include the start time as a sample. This is important because we want to evaluate the visibility of the target at the start time as well.
    offsets = np.arange(n_samples) * cadence_minutes * u.min                    #creates an array of time offsets spaced by cadence. 
    times = start + offsets                                                     # times array contains the actual observation times at which the visibility of the target will be evaluated.
    target = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs")     #defining the astronomical target

    results = []
    for name, site in OBSERVATORIES.items():                                        # OBSERVATORIES.items() returns a dictionary within a dictionary. The keys are the names and site is the values dictionary. 
        location = site["location"]
        frame = AltAz(obstime=times, location=location)                             #AltAz(altirude,azimuth) describe where an object appears in the local sky
        target_altaz = target.transform_to(frame)                                   #the target's position will change based on the observer's location and the time. So astropy will construct a new AltAz frame for everytime in the observation time grid. 
        altitude = target_altaz.alt.to_value(u.deg)                                 #calculates the target's altitude at each time sample. 
        sun_altitude = get_sun(times).transform_to(frame).alt.to_value(u.deg)   #newline
        moon_altitude = get_body("moon", times, location=location).transform_to(frame).alt.to_value(u.deg)
        #Note:get_sun() calculates the Sun's geocentric position (position relative to the center of the earth).
        #while get_body() can calculate the Moon's apparent position for a specific observatory. The Moon is different because its apparent position is more sensitive to the observer's location due to its relatively close distance to Earth.
        
        visible = altitude >= min_altitude_deg
        if require_astronomical_darkness:                                           #this checks an additional condition
            sun_altitude = get_sun(times).transform_to(frame).alt.to_value(u.deg)   #get_sun(times) calculates the Sun's position at the specified times. 
            visible &= sun_altitude <= -18.0                                        #this creates a boolean array called 'visible' that checks two conditions: 1. Target's altitude is above the minimum and 2. Sun's altitude is below -18 degrees. The &= operator updates the visible array in place, ensuring that only samples meeting both criteria are marked as True.
                                                                                    # This gives a boolean array.
        windows = _find_windows(times, visible)                                     # times:observation time grid, visible:boolean array indicating whether the target is visible at each time sample. 
        # building results for each observatory. results is a list of dictionaries.
        # Note: Maximum target altitude by observatory is the highest elevation angle (in degrees) that your astronomical target reaches above the horizon during the selected observation period, as viewed from each observatory
        # The minimum target altitude is the lowest elevation angle (in degrees) that your astronomical target must reach above the horizon for an observatory to consider it observable. 20 degrees: Reasonable general observing constraint
      
        results.append({
            "observatory": name,
            "observable": bool(np.any(visible)),                                    # checks if the target is observable at any time sample. Returns True or False.
            "max_altitude_deg": round(float(np.max(altitude)), 2),
            "visible_sample_count": int(np.sum(visible)),                           # counts the number of time samples where the target is visible.
            "visibility_windows": windows,
            "target_altitude": altitude.tolist(),    #newline
            "sun_altitude": sun_altitude.tolist(),   #newline
            "moon_altitude": moon_altitude.tolist(),    #newline
            "Times": times.utc.isot.tolist(),                 #newline
            "constraints": {
                "minimum_target_altitude_deg": min_altitude_deg,
                "astronomical_darkness_required": require_astronomical_darkness,
                "sun_altitude_limit_deg": -18.0 if require_astronomical_darkness else None,
                "cadence_minutes": cadence_minutes,
            },
        })

    return {
        "target": {
            "ra_deg": ra_deg,
            "dec_deg": dec_deg,
            "frame": "ICRS",
        },
        "search": {
            "start_utc": start.utc.isot,
            "end_utc": (start + duration_hours * u.hour).utc.isot,
            "duration_hours": duration_hours,
        },
        "results": results,
        "limitations": [
            #"This prototype models ground-based sites only.",
            #"Visibility windows are sampled at the requested cadence; boundaries are approximate.",
            #"Weather, horizon masks, instrument availability, slew time, and scheduling conflicts are not modeled.",
            #"Space-mission visibility requires mission-specific orbit, attitude, and operational constraints.",
            "Weather, observatory availability, slew time and scheduling conflicts are not modeled.",
            "Space-mission visibility requires specific orbit information, altitudes and operational constraints which can be added to a later versions of the model.",
            "Currently only a few ground-based optical observatories are added with the ability to add more observatories in future versions."
        ],
    }
